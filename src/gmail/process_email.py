from db.transaction_data import add_data_db
from llm.llm_integration import extract_data
from utils.data_processing import extract_text_from_payload, clean_text
from utils.modify_history import save_last_history, load_last_history

ALLOWED_SENDERS = [
    "alerts@axisbank.com",
]
KEYWORDS = ["credited", "debited"]

processed_message_ids = set()
PROCESSED_LIMIT = 1000  # max number of message IDs to keep


def process_new_emails(service, incoming_history_id):
    last_history_id = load_last_history()

    # If it's the very first run, just update last_history_id and return
    if not last_history_id:
        print("First run, saving initial history ID only.")
        save_last_history(incoming_history_id)
        return

    # Fetch history from Gmail
    response = service.users().history().list(
        userId="me",
        startHistoryId=last_history_id,
        historyTypes=["messageAdded"],
        labelId="INBOX"
    ).execute()

    history = response.get("history", [])
    if not history:
        print("No new messages found.")
    else:
        for record in history:
            for message in record.get("messages", []):
                msg_id = message["id"]

                # Skip if we've already processed this message
                if msg_id in processed_message_ids:
                    continue

                # Fetch full message details
                msg = service.users().messages().get(
                    userId="me", id=msg_id, format="full"
                ).execute()

                headers = msg["payload"]["headers"]
                subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
                sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown Sender")
                raw_body = extract_text_from_payload(msg["payload"])
                text_body = clean_text(raw_body)
                snippet = msg.get("snippet", "")

                # Example filtering (customize as needed)
                sender_ok = any(s.lower() in sender.lower() for s in ALLOWED_SENDERS)
                keyword_ok = any(k in text_body.lower() for k in KEYWORDS)

                if sender_ok and keyword_ok:
                    print("Text", text_body, '\n')

                    # Add to processed set with size limit
                    processed_message_ids.add(msg_id)
                    if len(processed_message_ids) > PROCESSED_LIMIT:
                        print(f"Processed message cache exceeded {PROCESSED_LIMIT}, clearing...")
                        processed_message_ids.clear()

                    # Uncomment for actual DB/LLM actions
                    data = extract_data(text_body)
                    print("Data", data, '\n')
                    #add_data_db(data)

    # Always update history ID after processing
    new_history_id = response.get("historyId", incoming_history_id)
    save_last_history(new_history_id)
