import firebase_admin
from firebase_admin import credentials, messaging
import os
import json
from decouple import config

# Path to the service account key
firebase_json = config("FIREBASE_SERVICE_ACCOUNT")
if not firebase_json:
    raise RuntimeError("FIREBASE_SERVICE_ACCOUNT env variable not set")

# Initialize only once
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(firebase_json))
    firebase_admin.initialize_app(cred)

# Must match the notifee channel the app creates in notificationService.js.
# Without an explicit channel, a push delivered while the app is backgrounded
# lands in FCM's fallback channel, which is LOW importance on most devices: it
# arrives, but silently and collapsed, which reads as "no notification".
ANDROID_CHANNEL_ID = "default"


def send_fcm_notification(token, title, body, data=None):
    """
    Sends a push notification using Firebase Cloud Messaging.
    :param token: FCM registration token (device-specific).
    :param title: Notification title.
    :param body: Notification body text.
    :param data: Optional custom data (dict). Values are coerced to strings.
    """
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=token,
        # FCM rejects a data payload containing any non-string value, and the
        # whole send fails rather than the offending key being dropped.
        data={k: str(v) for k, v in (data or {}).items()},
        android=messaging.AndroidConfig(
            priority="high",
            notification=messaging.AndroidNotification(
                channel_id=ANDROID_CHANNEL_ID,
                sound="default",
            ),
        ),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(sound="default"),
            ),
        ),
    )

    try:
        response = messaging.send(message)
        print(f"✅ Successfully sent notification: {response}")
        return response
    except (messaging.UnregisteredError, messaging.SenderIdMismatchError) as e:
        # The token belongs to an uninstalled app, cleared app data, or another
        # Firebase project. It will never deliver again, so drop the row instead
        # of retrying it on every future push.
        print(f"🗑️ Dropping dead FCM token {token[:20]}…: {e}")
        _delete_token(token)
        return None
    except Exception as e:
        print(f"❌ Error sending notification: {e}")
        return None


def _delete_token(token):
    # Imported here rather than at module scope: this module is imported from
    # several views, and a top-level model import would run before the app
    # registry is ready in some start-up orders.
    from firebase.models import DeviceToken

    DeviceToken.objects.filter(token=token).delete()


def notify_user(user, title, body, data=None):
    """
    Push to every device registered for `user`. Returns how many sends
    succeeded, so a caller can tell "delivered" from "nobody was reachable" —
    a distinction the old per-view loops threw away.
    """
    from firebase.models import DeviceToken

    tokens = list(
        DeviceToken.objects.filter(user=user).values_list("token", flat=True)
    )
    if not tokens:
        print(f"⚠️ No device tokens registered for {user.email} — nothing to push")
        return 0

    sent = 0
    for token in tokens:
        if send_fcm_notification(token=token, title=title, body=body, data=data):
            sent += 1

    print(f"📨 Pushed to {sent}/{len(tokens)} devices for {user.email}")
    return sent
