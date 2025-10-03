import json
import os

from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.cloud import pubsub_v1
from google.oauth2 import service_account

from gmail.process_email import process_new_emails

load_dotenv()

service_path = os.getenv('SERVICE')
service = json.loads(service_path)

def pull_new_messages(creds, subscription_path):
    credentials = service_account.Credentials.from_service_account_info(
        service
    )
    subscriber = pubsub_v1.SubscriberClient(credentials=credentials)

    def callback(message):
        try:
            data = json.loads(message.data.decode('utf-8'))
            history_id = data.get('historyId')
            if history_id:
                service = build('gmail', 'v1', credentials=creds)
                process_new_emails(service, history_id)
            message.ack()  # Acknowledge ONLY after success
        except Exception as e:
            #print("Error: ", e)
            message.nack()  # Retry if failure

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    print(f"Listening for messages on {subscription_path}...\n")

    try:
        streaming_pull_future.result()
    except KeyboardInterrupt:
        streaming_pull_future.cancel()