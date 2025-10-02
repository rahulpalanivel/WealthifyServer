import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
filepath = os.path.join(BASE_DIR,'data.json')

def save_last_history(history_id):
    new_data = {"HISTORY": history_id }
    with open(filepath, "w") as file:
        json.dump(new_data, file)



def load_last_history():
    with open(filepath, "r") as file:
        data = json.load(file)
    history_json = data['HISTORY']
    if history_json:
        return history_json
    return None
