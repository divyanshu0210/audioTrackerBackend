# views.py
import requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .models import  AssignedVideo
from mentor_mentee.models import Mentorship, User
from collections import defaultdict


# NOTIFICATION_SERVER_URL = "http://10.11.26.220:1000/notifications/create/"
NOTIFICATION_SERVER_URL = "https://at-notif-backend0210.onrender.com/notifications/create/"

@api_view(['POST'])
def assign_videos_to_mentees(request):
    mentor_id = request.data.get('mentor_id')
    mentee_gmails = request.data.get('mentee_gmails')
    videos = request.data.get('videos')

    if not mentor_id or not mentee_gmails or not videos:
        return Response({'error': 'mentor_id, mentee_gmails, and videos are all required.'}, status=400)

    try:
        mentor = User.objects.get(id=mentor_id)
    except User.DoesNotExist:
        return Response({'error': f'Mentor with id {mentor_id} does not exist.'}, status=404)

    # Fetch mentees by email
    mentees = User.objects.filter(email__in=mentee_gmails)
    found_emails = set(mentees.values_list('email', flat=True))
    not_found_emails = set(mentee_gmails) - found_emails

    if not_found_emails:
        return Response({'error': f'No users found for emails: {list(not_found_emails)}'}, status=404)

    # Validate mentorships
    mentee_ids = list(mentees.values_list('id', flat=True))
    mentorships = Mentorship.objects.filter(mentor=mentor, mentee_id__in=mentee_ids)
    valid_mentee_ids = set(mentorships.values_list('mentee_id', flat=True))
    email_map = {user.id: user.email for user in mentees}
    invalid_mentees = [email_map[mentee_id] for mentee_id in mentee_ids if mentee_id not in valid_mentee_ids]

    if invalid_mentees:
        return Response({'error': f'Mentor is not assigned to mentee(s): {invalid_mentees}'}, status=403)

    created = []
    for mentorship in mentorships:
        for video in videos:
            video_id = video.get('video_id')
            video_type = video.get('video_type')

            if not video_id or not video_type:
                continue  # Skip invalid input

            obj, is_created = AssignedVideo.objects.get_or_create(
                mentorship=mentorship,
                video_id=video_id,
                video_type=video_type,
            )
            if is_created:
                created.append({
                    'mentee_email': mentorship.mentee.email,
                    'video_id': video_id,
                    'video_type': video_type,
                })

        try:
            notif_payload = {
                "sender_id": mentor.id,
                "receiver_id": mentorship.mentee.id,
                "sender_name": mentor.full_name,
                "receiver_name": mentorship.mentee.full_name,
                "type": "assignment",
            }
            notif_response = requests.post(NOTIFICATION_SERVER_URL, json=notif_payload)
            if notif_response.status_code != 201:
                print("Notification server error:", notif_response.text)
        except Exception as e:
            print("Failed to send notification:", e)
  

    return Response({
        'assigned_count': len(created),
        'assignments': created
    }, status=201)



@api_view(['GET'])
def get_assignments_for_mentee(request):
    mentee_id = request.query_params.get('mentee_id')

    if not mentee_id:
        return Response({'error': 'mentee_id is required as a query parameter.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        mentee = User.objects.get(id=mentee_id)
    except User.DoesNotExist:
        return Response({'error': 'Mentee not found.'}, status=status.HTTP_404_NOT_FOUND)

    mentorships = Mentorship.objects.filter(mentee=mentee)
    if not mentorships.exists():
        return Response({'message': 'No assignments found for this mentee.'}, status=status.HTTP_200_OK)

    assignments = AssignedVideo.objects.filter(mentorship__in=mentorships,status='pending').select_related('mentorship__mentor')

    grouped_data = defaultdict(list)
    for a in assignments:
        mentor = a.mentorship.mentor
        mentor_key = f"{mentor.full_name} ({mentor.email})"
        grouped_data[mentor_key].append({
            'video_id': a.video_id,
            'video_type': a.video_type,
            'created_at': a.created_at,
        })

    assignments.update(status='sent')

    return Response({
        'mentee_id': mentee.id,
        'mentee_email': mentee.email,
        'total_mentors': len(grouped_data),
        'assignments_by_mentor': grouped_data,
    }, status=status.HTTP_200_OK)



@api_view(['GET'])
def get_pending_assignments_count_for_mentee(request):
    mentee_id = request.query_params.get('mentee_id')

    if not mentee_id:
        return Response({'error': 'mentee_id is required as a query parameter.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        mentee = User.objects.get(id=mentee_id)
    except User.DoesNotExist:
        return Response({'error': 'Mentee not found.'}, status=status.HTTP_404_NOT_FOUND)

    mentorships = Mentorship.objects.filter(mentee=mentee)
    if not mentorships.exists():
        return Response({'message': 'No assignments found for this mentee.'}, status=status.HTTP_200_OK)

    assignments = AssignedVideo.objects.filter(mentorship__in=mentorships,status='pending').select_related('mentorship__mentor')

    return Response({
        'mentee_id': mentee.id,
        'pending_assignments_count': assignments.count(),
    }, status=status.HTTP_200_OK)