import os
from twilio.rest import Client

def send_sms(to, body):
    try:
        account_sid = os.getenv("TWILIO_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        sender = os.getenv("TWILIO_PHONE")
        client = Client(account_sid, auth_token)
        message = client.messages.create(body=body, from_=sender, to=to)
        return message.sid
    except Exception as e:
        print("SMS error:", e)