import json
from googleapiclient.discovery import build
from google.cloud import pubsub_v1
from google.oauth2 import service_account

from src.gmail.process_email import process_new_emails

def pull_new_messages(creds, subscription_path):
    credentials = service_account.Credentials.from_service_account_file(
        r'Secrets\wealthifyService.json'
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