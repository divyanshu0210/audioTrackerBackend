import firebase_admin
from firebase_admin import credentials, messaging
import os
import json

# Path to the service account key
firebase_json = os.getenv("FIREBASE_SERVICE_ACCOUNT")
if not firebase_json:
    raise RuntimeError("FIREBASE_SERVICE_ACCOUNT env variable not set")

# Initialize only once
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(firebase_json))
    firebase_admin.initialize_app(cred)

def send_fcm_notification(token, title, body, data=None):
    """
    Sends a push notification using Firebase Cloud Messaging.
    :param token: FCM registration token (device-specific).
    :param title: Notification title.
    :param body: Notification body text.
    :param data: Optional custom data (dict).
    """
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=token,
        data=data or {}
    )

    try:
        response = messaging.send(message)
        print(f"✅ Successfully sent notification: {response}")
        return response
    except Exception as e:
        print(f"❌ Error sending notification: {e}")
        return None
