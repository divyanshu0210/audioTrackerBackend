from notifications.models import Notification


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
