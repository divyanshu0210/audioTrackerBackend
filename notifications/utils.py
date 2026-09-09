from notifications.models import Notification


def push_notification(notification: Notification, receiver) -> int:
    """
    Push `notification` to every device belonging to `receiver`.

    Title and body come from the same two helpers the in-app list uses, so the
    push and the row the app fetches later always read identically — the four
    call sites used to each build their own copy, and the assignment one had
    drifted to a different wording showing an email instead of a name.
    """
    # Local import: firebase's fcm module reaches back into the notification
    # helpers, and importing it at module scope would close the loop.
    from firebase.firebaseUtils.fcm import notify_user

    title = get_notification_title_by_type(notification.type)
    body = get_notification_body(notification)

    return notify_user(
        user=receiver,
        title=title,
        body=body,
        # Carried so the app can route a tap to the right screen, and so its
        # foreground handler has a fallback source for the text if it ever
        # receives a data-only message.
        data={
            "notification_id": notification.id,
            "type": notification.type,
            "sender_id": notification.sender_id,
            "sender_name": notification.sender_name,
            "title": title,
            "body": body,
        },
    )


def get_notification_body(notification: Notification) -> str:
    sender_name = notification.sender_name
    notif_type = notification.type

    if notif_type == "mentor":
        return f"{sender_name} has created a new MentorMentee request."
    elif notif_type == "mentee":
        return f"{sender_name} has created a new MentorMentee request."
    elif notif_type == "assignment":
        return f"You have received new assignments from {sender_name}."
    elif notif_type == "report":
        return f"{sender_name} has submitted a report for your review."
    elif notif_type == "approved":
        return f"{sender_name} has approved your request."
    elif notif_type == "rejected":
        return f"{sender_name} has rejected your request."
    elif notif_type == "cancelled":
        return f"{sender_name} has cancelled their request."
    else:
        return f"You have a new notification from {sender_name}."


def get_notification_title_by_type(notif_type: str) -> str:
    if notif_type in ["mentor", "mentee"]:
        return "Mentor Mentee Request"
    elif notif_type == "assignment":
        return "New Assignment"
    elif notif_type == "report":
        return "Report Submitted"
    elif notif_type in ["approved", "rejected", "cancelled"]:
        return "Mentorship Status"
    else:
        return "Notification"
