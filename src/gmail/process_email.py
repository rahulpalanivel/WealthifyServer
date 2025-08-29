from llm.llm_integration import extract_data
from utils.data_processing import extract_text_from_payload, clean_text
from utils.modify_history import save_last_history, load_last_history

ALLOWED_SENDERS = [
    "alerts@axisbank.com",
]
KEYWORDS = ["credit", "debit"]

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
                    print(extract_data(text_body))

    # update historyId
    new_history_id = response.get("historyId", incoming_history_id)
    save_last_history(new_history_id)
