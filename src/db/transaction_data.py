import os
import json
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()

service_account_info = json.loads(os.getenv('FIRESTORE_SERVICE'))
cred = credentials.Certificate(service_account_info)
firebase_admin.initialize_app(cred)
db = firestore.client(database_id="weathify-db")


def add_data_db(data):
    var = db.collection('transactions').add(data)
    print("Data Integration Ended: ", var)

# if __name__ == '__main__':
#     data = {"type": "credit","amount": "1107.00","date": "08-11-2022","time": "09:27:32","Transaction Info": "UPI/P2M/55651234872/Academy"}
#     add_data_db(data)















