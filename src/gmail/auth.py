import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from utils.modify_history import save_last_history

from dotenv import load_dotenv, set_key

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def authenticate_gmail():
    creds = None
    tokens_path = os.getenv('TOKEN')
    tokens = json.loads(tokens_path)
    if tokens:
        creds = Credentials.from_authorized_user_info(tokens, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            secrets_path = os.getenv('GOOGLE_SECRETS')
            secrets = json.loads(secrets_path)
            flow = InstalledAppFlow.from_client_config(secrets, SCOPES)
            creds = flow.run_local_server()
        set_key(os.path.join(BASE_DIR,'.env'), 'TOKEN', creds.to_json())
    return creds


def watch_gmail(service):
    topic_name = os.getenv('TOPIC')
    request = {
        'labelIds': ['INBOX'],
        'topicName': topic_name
    }
    response = service.users().watch(userId='me', body=request).execute()
    history_id = response.get("historyId")
    if history_id:
        save_last_history(history_id)
    print("Watch set. Expiration:", response.get('expiration'), "Initial historyId:", history_id)