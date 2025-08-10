import os
import base64
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from google import genai
from google.genai import types

import re

from pymongo.mongo_client import MongoClient

# If modifying scopes, delete the file token.json
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    creds = None

    # 1. Load existing credentials if available
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # 2. If no credentials or invalid, refresh or do manual auth once
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh automatically
            creds.refresh(Request())
        else:
            # First-time manual authentication (browser login)
            flow = InstalledAppFlow.from_client_secrets_file('googleSecrets.json', SCOPES)
            creds = flow.run_local_server()

        # 3. Save the credentials (includes refresh token) for next run
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

def format_json(text:str):
    if text.__contains__("```json"):
        text = text.split("```json")[1]
        text = text.split("```")[0]
    return text
    
    
def get_emails(service, sender_email):
    query = f'from:{sender_email}'
    messages = []
    next_page_token = None

    while True:
        response = service.users().messages().list(
            userId='me',
            q=query,
            pageToken=next_page_token,
            maxResults=10  # max allowed per request
        ).execute()

        messages.extend(response.get('messages', []))
        next_page_token = response.get('nextPageToken')

        if not next_page_token:
            break

    email_list = []
 
    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
        headers = msg['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
        raw_body  = extract_text_from_payload(msg['payload'])
        text_body = clean_text(raw_body).strip()
        snippet = str(msg['snippet'])

        if text_body.lower().__contains__("credit") or text_body.lower().__contains__("debit") or snippet.lower().__contains__("credit") or snippet.lower().__contains__("debit"):
            email_list.append({
                'subject': subject,
                'from': sender,
                'body': text_body,
                'snippet': snippet
            })

    return email_list

def llm_response(data):
    with open('api_key.json', 'r') as file:
        key = json.load(file)
    apiKey = key['api_key']
    client = genai.Client(api_key=apiKey)
    text = data
    fields=["type", "amount", "date", "time", "Transaction Info"]
    response = client.models.generate_content(
        model="gemma-3-1b-it",
        contents =
        f"""You are a helpful AI Assistant, from a given text extracts the required fields.
        Text:{text}
        Fields:{fields}
        Do not provide any explanations.
        Return the output in the below provided JSON format only.
        Below is an example provided, Return the output based on the JSON format of the given example.
        {
            {
                "type": "credit",
                "amount": "1107.00",
                "date": "08-11-2022",
                "time": "09:27:32",
                "Transaction Info": "UPI/P2M/55651234872/Academy"
            }
        }
        """
    )
    return format_json(response.text)

def addToMongodb(data):
        
    uri = "mongodb+srv://palanivelrahul45:cNJ3NjCyqHrn1S3n@transactiondata.dyvlroy.mongodb.net/?retryWrites=true&w=majority&appName=TransactionData"

    client = MongoClient(uri)

    db = client["TransactionDb"]
    collection = db["TransactionCollection(UnStructured)"]

    collection.insert_many(data)

def main():
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)

    sender_email = 'alerts@axisbank.com'
    emails = get_emails(service, sender_email)

    data = []
    for mail in emails:
        #res = llm_response(mail)
        data.append(mail)
    print(data)
    #addToMongodb(data)
    



if __name__ == '__main__':
    main()
