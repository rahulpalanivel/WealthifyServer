import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from src.utils.modify_history import save_last_history


SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    creds = None
    if os.path.exists(r'Secrets\token.json'):
        creds = Credentials.from_authorized_user_file(r'Secrets\token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(r'Secrets\googleSecrets.json', SCOPES)
            creds = flow.run_local_server()
        with open(r'Secrets\token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


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