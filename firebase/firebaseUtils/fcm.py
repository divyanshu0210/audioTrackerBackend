import firebase_admin
from firebase_admin import credentials, messaging
import os

# Path to the service account key
FIREBASE_CERT_PATH = os.path.join(os.path.dirname(__file__), "serviceAccountKey.json")

# Initialize only once
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CERT_PATH)
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
