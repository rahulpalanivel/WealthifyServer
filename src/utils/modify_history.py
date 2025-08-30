import json
import os
from dotenv import load_dotenv, set_key

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def save_last_history(history_id):
    set_key(os.path.join(BASE_DIR,'.env'), "HISTORY", str(history_id))

def load_last_history():
    history_json = os.getenv("HISTORY")
    if history_json:
        return history_json
    return None