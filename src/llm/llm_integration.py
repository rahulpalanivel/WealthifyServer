import os
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv('API_KEY'))
fields=["type", "amount", "date", "time", "Transaction Info"]

def extract_data(text):
    time.sleep(3)
    prompt = f"""You are a helpful AI Assistant, from a given text extracts the required fields.
            Text:{text}
            Fields:{fields}
            Do not provide any explanations.
            Return the output in the below provided JSON format only.
            Do not return the result in JSON markdown.
            Below is an example provided, Return the output based on the JSON format of the given example.
            {
                {
                    "type": "credit",
                    "amount": "1107.00",
                    "date": "08-11-2022",
                    "time": "09:27:32",
                    "Transaction Info": "UPI/P2M/55651234872/Academy"
                }
            }
            """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text
