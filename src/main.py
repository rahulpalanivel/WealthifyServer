from googleapiclient.discovery import build

from gmail.auth import authenticate_gmail, watch_gmail
from gmail.pub_sub import pull_new_messages

from dotenv import load_dotenv
import os


load_dotenv()

def main():
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)

    watch_gmail(service)
    subscription_path = os.getenv("SUBSCRIPTION_PATH")
    pull_new_messages(creds, subscription_path)

if __name__ == '__main__':
    main()
