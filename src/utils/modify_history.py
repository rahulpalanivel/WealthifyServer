import json
import os

HISTORY_FILE = r"Secrets\last_history.json"

def save_last_history(history_id):
    with open(HISTORY_FILE, "w") as f:
        json.dump({"historyId": history_id}, f)

def load_last_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f).get("historyId")
    return None