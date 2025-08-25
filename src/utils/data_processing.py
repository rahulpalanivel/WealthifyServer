import base64
import re

def extract_text_from_payload(payload):
    if payload.get('mimeType') == 'text/plain' and payload.get('body', {}).get('data'):
        data = payload['body']['data']
        return base64.urlsafe_b64decode(data).decode('utf-8')

    if 'parts' in payload:
        for part in payload['parts']:
            result = extract_text_from_payload(part)
            if result:
                return result
    return ""


def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip().split('****This')[0]