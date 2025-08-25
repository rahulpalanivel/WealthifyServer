from googleapiclient.discovery import build

from src.gmail.auth import authenticate_gmail, watch_gmail
from src.gmail.pub_sub import pull_new_messages

def main():
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)

    watch_gmail(service)  # sets up watch + stores initial historyId
    subscription_path = "projects/wealthify-467717/subscriptions/Wealthify-sub"
    pull_new_messages(creds, subscription_path)

if __name__ == '__main__':
    main()
