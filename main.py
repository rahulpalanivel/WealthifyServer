import os
import base64
import json
import re
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from pymongo.mongo_client import MongoClient
from google.cloud import pubsub_v1
from google.oauth2 import service_account

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
HISTORY_FILE = "last_history.json"

# ---------------- Config ----------------
ALLOWED_SENDERS = [
    "alerts@axisbank.com",
]
KEYWORDS = ["credit", "debit"]

# ---------------- Gmail Authentication ----------------
def authenticate_gmail():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('googleSecrets.json', SCOPES)
            creds = flow.run_local_server()
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

# ---------------- Helpers ----------------
def extract_text_from_payload(payload):
    if payload.get('mimeType') == 'text/plain' and payload.get('body', {}).get('data'):
        data = payload['body']['data']
        return base64.urlsafe_b64decode(data).decode('utf-8')

    if 'parts' in payload:
        for part in payload['parts']:
            result = extract_text_from_payload(part)
            if result:
                return result
    return ""

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip().split('****This')[0]

def save_last_history(history_id):
    with open(HISTORY_FILE, "w") as f:
        json.dump({"historyId": history_id}, f)

def load_last_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f).get("historyId")
    return None

# ---------------- Gmail Watch Setup ----------------
def watch_gmail(service):
    topic_name = 'projects/wealthify-467717/topics/Wealthify'
    request = {
        'labelIds': ['INBOX'],
        'topicName': topic_name
    }
    response = service.users().watch(userId='me', body=request).execute()
    history_id = response.get("historyId")
    if history_id:
        save_last_history(history_id)
    print("Watch set. Expiration:", response.get('expiration'), "Initial historyId:", history_id)

# ---------------- Process New Emails ----------------
def process_new_emails(service, incoming_history_id):
    last_history_id = load_last_history()
    if not last_history_id:
        print("No stored historyId, saving current one and skipping...")
        save_last_history(incoming_history_id)
        return

    response = service.users().history().list(
        userId='me',
        startHistoryId=last_history_id,
        historyTypes=['messageAdded'],
        labelId='INBOX'
    ).execute()

    history = response.get('history', [])
    if not history:
        print("No new messages found.")
    else:
        for record in history:
            messages = record.get('messages', [])
            for message in messages:
                msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
                headers = msg['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                raw_body = extract_text_from_payload(msg['payload'])
                text_body = clean_text(raw_body)
                snippet = msg.get('snippet', '')

                # ---- Filtering ----
                sender_ok = any(allowed.lower() in sender.lower() for allowed in ALLOWED_SENDERS)
                keyword_ok = any(k in text_body.lower() or k in subject.lower() or k in snippet.lower() for k in KEYWORDS)

                if sender_ok and keyword_ok:
                    print("\n✅ Matched Email")
                    print("From:", sender)
                    print("Subject:", subject)
                    print("Body:", text_body)
                    print("Snippet:", snippet)
                else:
                    print("\n⏩ Skipped Email:", subject, "from", sender)

    # update historyId
    new_history_id = response.get("historyId", incoming_history_id)
    save_last_history(new_history_id)

# ---------------- Pub/Sub Pull ----------------
def pull_new_messages(creds, subscription_path):
    credentials = service_account.Credentials.from_service_account_file(
        'wealthifyService.json'
    )
    subscriber = pubsub_v1.SubscriberClient(credentials=credentials)

    def callback(message):
        try:
            data = json.loads(message.data.decode('utf-8'))
            history_id = data.get('historyId')
            if history_id:
                service = build('gmail', 'v1', credentials=creds)
                process_new_emails(service, history_id)
            message.ack()
        except Exception as e:
            print("Error processing message:", e)
            message.nack()

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    print(f"Listening for messages on {subscription_path}...\n")

    try:
        streaming_pull_future.result()
    except KeyboardInterrupt:
        streaming_pull_future.cancel()

# ---------------- Main ----------------
def main():
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)

    watch_gmail(service)  # sets up watch + stores initial historyId
    subscription_path = "projects/wealthify-467717/subscriptions/Wealthify-sub"
    pull_new_messages(creds, subscription_path)

if __name__ == '__main__':
    main()
