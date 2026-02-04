from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Notification
from .serializers import NotificationSerializer
import logging
from django.db.models import Q

logger = logging.getLogger(__name__)  # You can configure this logger in your Django settings


@api_view(['GET'])
def get_pending_notifications(request):
    receiver_id = request.query_params.get('receiver_id')
    print(receiver_id,"get_pending_notifications")
    if not receiver_id:
        return Response({"error": "receiver_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    # Fetch pending notifications
    notifications = Notification.objects.filter(receiver_id=str(receiver_id), status='pending')
    print(notifications,"get_pending_notifications")
    serializer = NotificationSerializer(notifications, many=True)
    print(serializer.data,"get_pending_notifications")

    notifications.update(status='sent')

    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_sent_notifications(request):
    receiver_id = request.query_params.get('receiver_id')
    print(receiver_id,"get_sent_notifications")
    if not receiver_id:
        return Response({"error": "receiver_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    # Fetch pending notifications
    notifications = Notification.objects.filter(
        Q(receiver_id=str(receiver_id)) & 
        (Q(status='sent') | (Q(status='viewed') & Q(id__in=Notification.objects.filter(
            receiver_id=str(receiver_id), 
            status='viewed'
        ).order_by('-created_at')[:10]))
    )).order_by('-created_at')
   
    serializer = NotificationSerializer(notifications, many=True)

    # notifications.update(status='viewed')

    return Response(serializer.data, status=status.HTTP_200_OK)



@api_view(['GET'])
def get_sent_notifications_count(request):
    receiver_id = request.query_params.get('receiver_id')
    print(receiver_id,"get_sent_notifications_count")
    if not receiver_id:
        return Response({"error": "receiver_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    notifications = Notification.objects.filter(receiver_id=str(receiver_id), status='sent')
    return Response({'sent_notifications_count':notifications.count()}, status=status.HTTP_200_OK)

@api_view(['POST'])  # Use POST since we're modifying data
def mark_notifications_as_viewed(request):
    receiver_id = request.data.get('receiver_id')
    print(receiver_id,"mark_notifications_as_viewed")

    if not receiver_id:
        return Response({"error": "receiver_id is required."}, status=status.HTTP_400_BAD_REQUEST)
    # Get notifications with status='sent' for this receiver
    notifications = Notification.objects.filter(receiver_id=str(receiver_id), status='sent')
    print(f"Found {notifications.count()} notifications to mark as viewed")
    # Update them to 'viewed'
    notifications.update(status='viewed')

    return Response({"message": "Notifications marked as viewed."}, status=status.HTTP_200_OK)


def keep_alive(request):
    return JsonResponse({
        "status": "ok",
        "message": "server alive",
    })