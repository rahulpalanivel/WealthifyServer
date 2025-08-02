import os
import base64
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from requests import Request
import re

# If modifying scopes, delete the file token.json
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    creds = None
    # Load credentials if available
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # Otherwise, go through OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('D:\Projects\ML-DL\Wealthify\googleSecrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save token for later use
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def extract_text_from_payload(payload):
    # Recursively get text/plain content
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
    # Remove excessive newlines, tabs, and spaces
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces/newlines/tabs with single space
    return text.strip().split('****This')[0]

def get_emails(service, max_results):
    query = 'alerts@axisbank.com'
    results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
    messages = results.get('messages', [])

    email_list = []

    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
        headers = msg['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
        raw_body  = extract_text_from_payload(msg['payload'])
        text_body = clean_text(raw_body)

        email_list.append({
            'subject': subject,
            'from': sender,
            'body': text_body.strip()
        })

    return email_list

def main():
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)

    emails = get_emails(service, max_results=10)
    for i, email in enumerate(emails, 1):
        print(f"\n--- Email {i} ---")
        print("From:", email['from'])
        print("Subject:", email['subject'])
        print("body:", email['body'])

if __name__ == '__main__':
    main()
