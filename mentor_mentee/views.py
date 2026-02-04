
import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserSerializer
from .models import User, MentorshipRequest, Mentorship
from .serializers import *
from notifications.models import *
from notifications.utils import *
from firebase.models import *
from firebase.firebaseUtils.fcm import send_fcm_notification

# NOTIFICATION_SERVER_URL = "http://10.11.26.220:1000/notifications/create/"
NOTIFICATION_SERVER_URL = "https://at-notif-backend0210.onrender.com/notifications/create/"


@api_view(['POST'])
def create_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def list_users(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)

# //////////////////////////////////////////////////////////////////
@api_view(['POST'])
def check_email(request):
    email = request.data.get('email')
    print(f"Checking email: {email}")

    if not email:
        return Response({'error': 'Email is required'}, status=400)

    try:
        user = User.objects.get(email=email)
        return Response({
            'message': 'User exists',
            'user_id': user.id,
            'full_name': user.full_name,
            'email': user.email
        }, status=200)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)


# //////////////////////////////////////////////////////////////////


@api_view(['POST'])
def send_mentorship_request(request):
    sender_id = request.data.get('sender_id')
    receiver_email = request.data.get('receiver_email')
    request_type = request.data.get('request_type')  # 'mentor' or 'mentee'
    print(sender_id,receiver_email,request_type)

    try:
        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(email=receiver_email)
    except User.DoesNotExist:
        return Response({'error': 'Sender or receiver does not exist'}, status=400)
    
    if(sender.id==receiver.id):
         return Response({'error': 'Request cannot be send to self'}, status=400)

    # Check if request already exists from sender to receiver
    existing_request = MentorshipRequest.objects.filter(sender=sender, receiver=receiver).first()
    if existing_request:
        if existing_request.status == "rejected":
            existing_request.delete()
        else :   
            return Response({
                'error': f"{existing_request.receiver.full_name} is already the {existing_request.type} of {existing_request.sender.full_name}"
            }, status=400)

    # Check if reverse request exists (receiver already sent one to sender)
    reverse_request = MentorshipRequest.objects.filter(sender=receiver, receiver=sender).first()
    if reverse_request:
        if reverse_request.status == "rejected":
            reverse_request.delete()
        else :
            return Response({
                'error': f"{reverse_request.receiver.full_name} is already the {reverse_request.type} of {reverse_request.sender.full_name}"
            }, status=400)

    request_obj = MentorshipRequest.objects.create(
        sender=sender,
        receiver=receiver,
        type = request_type,
    )


    notification = Notification.objects.create(
            sender_id=sender.id,
            receiver_id=receiver.id,
            sender_name=sender.full_name,
            receiver_name=receiver.full_name,
            type=request_type,
            status='pending',
        )
    
    notif_title = get_notification_title_by_type(request_type)
    notif_body= get_notification_body(notification)

    tokens = DeviceToken.objects.filter(user=receiver).values_list("token", flat=True)
    for token in tokens:
        send_fcm_notification(
            token=token,
            title=notif_title,
            body=notif_body
        )
    # notification.status = 'sent'
    # notification.save()


    return Response({'message': 'Request sent successfully'}, status=201)

#API to accept/reject a request
@api_view(['POST'])
def respond_mentorship_request(request):
    request_id = request.data.get('request_id')
    action = request.data.get('action')  # 'approve' or 'reject'

    try:
        req = MentorshipRequest.objects.get(id=request_id)
        if action == 'approve':
            req.status = 'approved'
            if req.type =="mentor":
             Mentorship.objects.create(mentor=req.receiver, mentee=req.sender)
            if req.type =="mentee":
             Mentorship.objects.create(mentor=req.sender, mentee=req.receiver)
        elif action == 'reject':
            req.status = 'rejected'
        else:
            return Response({'error': 'Invalid action'}, status=400)
        
        req.save()

        notification = Notification.objects.create(
            sender_id=req.receiver.id,
            receiver_id=req.sender.id,
            sender_name=req.receiver.full_name,
            receiver_name=req.sender.full_name,
            type=req.status,
            status='pending',
        )
    
        notif_title = get_notification_title_by_type(req.status)
        notif_body= get_notification_body(notification)

        tokens = DeviceToken.objects.filter(user=req.sender).values_list("token", flat=True)
        for token in tokens:
            send_fcm_notification(
                token=token,
                title=notif_title,
                body=notif_body
            )
        # notification.status = 'sent'
        # notification.save()


        return Response({'message': f'Request {action}d successfully'})
    except MentorshipRequest.DoesNotExist:
        return Response({'error': 'Request not found'}, status=404)


#API to cancel a request
@api_view(['POST'])
def cancel_mentorship_request(request):
    request_id = request.data.get('request_id')
    try:
        req = MentorshipRequest.objects.get(id=request_id)
        
        notification = Notification.objects.create(
            sender_id=req.sender.id,
            receiver_id=req.receiver.id,
            sender_name=req.sender.full_name,
            receiver_name=req.receiver.full_name,
            type="cancelled",
            status='pending',
        )
    
        notif_title = get_notification_title_by_type("cancelled")
        notif_body= get_notification_body(notification)

        tokens = DeviceToken.objects.filter(user=req.receiver).values_list("token", flat=True)
        for token in tokens:
            send_fcm_notification(
                token=token,
                title=notif_title,
                body=notif_body
            )
        # notification.status = 'sent'
        # notification.save()


        req.delete()
        return Response({'message': 'Request cancelled successfully'})
    except MentorshipRequest.DoesNotExist:
        return Response({'error': 'Request not found'}, status=404)

    
#  API to fetch requests (sent & received)
@api_view(['GET'])
def get_mentorship_requests(request, user_id):
    sent = MentorshipRequest.objects.filter(sender_id=user_id,status='pending')
    received = MentorshipRequest.objects.filter(receiver_id=user_id,status='pending')

    return Response({
        'sent_requests': MentorshipRequestSerializer(sent, many=True).data,
        'received_requests': MentorshipRequestSerializer(received, many=True).data,
    })

@api_view(['GET'])
def get_mentors_and_mentees(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    # Mentees: People this user is mentoring
    mentees_qs = Mentorship.objects.filter(mentor=user).select_related('mentee')
    mentees = [mentorship.mentee for mentorship in mentees_qs]

    # Mentors: People mentoring this user
    mentors_qs = Mentorship.objects.filter(mentee=user).select_related('mentor')
    mentors = [mentorship.mentor for mentorship in mentors_qs]

    return Response({
        "mentors": UserSerializer(mentors, many=True).data,
        "mentees": UserSerializer(mentees, many=True).data
    })
    
# //////////////////////////////////////////////////////////////////
@api_view(['GET'])
def get_received_requests(request, user_id):
    requests = MentorshipRequest.objects.filter(receiver_id=user_id, status='pending')
    serializer = MentorshipRequestSerializer(requests, many=True)
    return Response(serializer.data)

# //////////////////////////////////////////////////////////////////


# @api_view(["POST"])
# def create_group(request):
#     mentee_ids = request.data.get("mentees", [])
#     if not mentee_ids or not isinstance(mentee_ids, list):
#         return Response(
#             {"error": "At least one mentee must be provided."},
#             status=status.HTTP_400_BAD_REQUEST
#         )

#     # Extract group data (without mentees)
#     group_data = {
#         "name": request.data.get("name"),
#         "mentor_id": request.data.get("mentor_id")
#     }
#     serializer = MentorGroupSerializer(data=group_data)

#     if serializer.is_valid():
#         group = serializer.save()

#         # Add mentees to group
#         memberships = []
#         for mentee_id in mentee_ids:
#             try:
#                 mentee = User.objects.get(pk=mentee_id)
#                 membership = GroupMembership.objects.create(group=group, mentee=mentee)
#                 memberships.append(membership)
#             except User.DoesNotExist:
#                 return Response(
#                     {"error": f"Mentee with id {mentee_id} does not exist."},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#         response_data = MentorGroupSerializer(group).data
#         response_data["mentees"] = [GroupMembershipSerializer(m).data for m in memberships]

#         return Response(response_data, status=status.HTTP_201_CREATED)

#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# # 2. Add a Mentee to a Group
# @api_view(["POST"])
# def add_mentee_to_group(request):
#     group_id = request.data.get("group_id")
#     mentee_ids = request.data.get("mentees", [])

#     if not group_id:
#         return Response({"error": "group_id is required."}, status=status.HTTP_400_BAD_REQUEST)

#     if not mentee_ids or not isinstance(mentee_ids, list):
#         return Response({"error": "At least one mentee must be provided."}, status=status.HTTP_400_BAD_REQUEST)

#     try:
#         group = MentorGroup.objects.get(pk=group_id)
#     except MentorGroup.DoesNotExist:
#         return Response({"error": f"Group with id {group_id} does not exist."}, status=status.HTTP_404_NOT_FOUND)

#     memberships = []
#     for mentee_id in mentee_ids:
#         try:
#             mentee = User.objects.get(pk=mentee_id)
#             membership, created = GroupMembership.objects.get_or_create(group=group, mentee=mentee)
#             memberships.append(membership)
#         except User.DoesNotExist:
#             return Response(
#                 {"error": f"Mentee with id {mentee_id} does not exist."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#     return Response(
#         {
#             "group": MentorGroupSerializer(group).data,
#             "added_mentees": [GroupMembershipSerializer(m).data for m in memberships],
#         },
#         status=status.HTTP_201_CREATED
#     )

# @api_view(["GET"])
# def list_groups_with_mentees(request, mentor_id):
#     groups = MentorGroup.objects.filter(mentor_id=mentor_id).prefetch_related("memberships__mentee")
#     serializer = GroupWithMenteesSerializer(groups, many=True)
#     return Response(serializer.data, status=status.HTTP_200_OK)


# @api_view(["GET"])
# def list_groups(request, mentor_id):
#     groups = MentorGroup.objects.filter(mentor_id=mentor_id)
#     serializer = MentorGroupListSerializer(groups, many=True)
#     return Response(serializer.data, status=status.HTTP_200_OK)


# # 2. Get details of a single group (with mentees)
# @api_view(["GET"])
# def group_detail(request, group_id):
#     try:
#         group = MentorGroup.objects.prefetch_related("memberships__mentee").get(pk=group_id)
#     except MentorGroup.DoesNotExist:
#         return Response({"error": "Group not found"}, status=status.HTTP_404_NOT_FOUND)

#     serializer = GroupDetailSerializer(group)
#     return Response(serializer.data, status=status.HTTP_200_OK)

# @api_view(["DELETE"])
# def delete_group(request, group_id):
#     try:
#         group = MentorGroup.objects.get(pk=group_id)
#         group.delete()  # Cascade will remove memberships too
#         return Response(
#             {"message": f"Group {group_id} deleted successfully."},
#             status=status.HTTP_204_NO_CONTENT
#         )
#     except MentorGroup.DoesNotExist:
#         return Response({"error": "Group not found"}, status=status.HTTP_404_NOT_FOUND)
    
# @api_view(["DELETE"])
# def remove_mentee_from_group(request, group_id, mentee_id):
#     try:
#         membership = GroupMembership.objects.get(group_id=group_id, mentee_id=mentee_id)
#         membership.delete()
#         return Response(
#             {"message": f"Mentee {mentee_id} removed from group {group_id} successfully."},
#             status=status.HTTP_204_NO_CONTENT
#         )
#     except GroupMembership.DoesNotExist:
#         return Response(
#             {"error": f"Mentee {mentee_id} is not part of group {group_id}."},
#             status=status.HTTP_404_NOT_FOUND
#         )
