# views.py
import requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .models import  AssignedVideo
from mentor_mentee.models import Mentorship, User
from collections import defaultdict
from notifications.models import *
from firebase.models import *
from notifications.utils import push_notification
from django.utils import timezone
from report.models import Video, VideoWatchReport


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
                # Not part of the lookup: the same video assigned twice is the
                # same assignment however the mentor got to it, and including
                # this would let one row become two.
                defaults={'origin_video_id': video.get('origin_video_id') or ''},
            )
            if is_created:
                created.append({
                    'mentee_email': mentorship.mentee.email,
                    'video_id': video_id,
                    'video_type': video_type,
                })

        notification = Notification.objects.create(
            sender_id=mentor.id,
            receiver_id=mentorship.mentee.id,
            sender_name=mentor.full_name,
            receiver_name=mentorship.mentee.full_name,
            type='assignment',
            status='pending',
        )

        push_notification(notification, mentorship.mentee)
        # notification.status = 'sent'
        # notification.save()

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
            # The id is what the app acknowledges with. Without it the only
            # way to confirm delivery would be to describe the video again,
            # which cannot tell apart two mentors assigning the same video.
            'id': a.id,
            'video_id': a.video_id,
            # The mentee needs both for a device assignment: the bytes come
            # from video_id (the Drive copy), the identity from this.
            'origin_video_id': a.origin_video_id,
            'video_type': a.video_type,
            'created_at': a.created_at,
        })

    # Deliberately *not* marked delivered here. Handing a row to a device is
    # not the same as that device managing to build the item: a failed Drive
    # resolve, a crash mid-loop or a dropped connection used to leave the
    # assignment flipped to 'sent' and never returned again, so it was gone for
    # good. These stay pending until acknowledge_assignments says otherwise,
    # which also makes this endpoint safe to retry.

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

@api_view(['POST'])
def acknowledge_assignments(request):
    """
    Called by the mentee's app once it has actually built the assigned items
    in its own database.

    Scoped to the mentee rather than trusting the ids alone: they are
    sequential, so without that filter anyone could mark another mentee's
    assignments delivered by guessing numbers.
    """
    mentee_id = request.data.get('mentee_id')
    assignment_ids = request.data.get('assignment_ids') or []

    if not mentee_id:
        return Response({'error': 'mentee_id is required.'}, status=400)
    if not assignment_ids:
        return Response({'acknowledged': 0}, status=200)

    updated = AssignedVideo.objects.filter(
        id__in=assignment_ids,
        mentorship__mentee_id=mentee_id,
        status='pending',
    ).update(status='delivered', delivered_at=timezone.now())

    return Response({'acknowledged': updated}, status=200)


def _merge_intervals(intervals):
    """
    [[start, end], ...] collapsed so overlapping parts appear once, in order.

    Returned as segments rather than just a total because the mentor's row
    draws them: which parts of a lecture were watched says more than how much
    of it was, and the two cannot be recovered from a percentage.
    """
    clean = []
    for pair in intervals or []:
        if not isinstance(pair, (list, tuple)) or len(pair) < 2:
            continue
        try:
            start, end = float(pair[0]), float(pair[1])
        except (TypeError, ValueError):
            continue
        if end > start:
            clean.append((start, end))

    if not clean:
        return []

    clean.sort()
    merged = []
    current_start, current_end = clean[0]
    for start, end in clean[1:]:
        if start <= current_end:
            current_end = max(current_end, end)
        else:
            merged.append([current_start, current_end])
            current_start, current_end = start, end
    merged.append([current_start, current_end])
    return merged


@api_view(['GET'])
def get_mentee_assignments_for_mentor(request):
    """
    What one mentor assigned to one mentee, with delivery state and how much of
    each video that mentee has watched.

    The watch figures come from the reports the mentee's app already uploads,
    so this adds no new tracking - it only joins what is there. Intervals are
    merged across every report row for a video: they are cumulative within a
    row, but a video watched over several days has one row per day, and taking
    only the latest would undercount if one day's upload never landed.
    """
    mentor_id = request.query_params.get('mentor_id')
    mentee_id = request.query_params.get('mentee_id')

    if not mentor_id or not mentee_id:
        return Response({'error': 'mentor_id and mentee_id are required.'}, status=400)

    mentorships = Mentorship.objects.filter(mentor_id=mentor_id, mentee_id=mentee_id)
    if not mentorships.exists():
        return Response({'error': 'No mentorship between these users.'}, status=403)

    assignments = list(
        AssignedVideo.objects.filter(mentorship__in=mentorships).order_by('-created_at')
    )
    if not assignments:
        return Response({'assignments': []}, status=200)

    # Watch reports are keyed by the id the *mentee* holds the item under, and
    # for a device assignment that is origin_video_id — video_id is the Drive
    # copy the bytes came from, which the mentee's app never records a report
    # against. Joining on video_id found nothing for those, so a device row
    # showed no progress bar at all however much had been watched.
    report_key = lambda a: a.origin_video_id or a.video_id

    # One query for the whole list rather than one per row.
    video_ids = {report_key(a) for a in assignments}
    reports = VideoWatchReport.objects.filter(
        user_id=mentee_id, video_id__in=video_ids
    ).values_list('video_id', 'watchedIntervals')

    intervals_by_video = defaultdict(list)
    for video_id, intervals in reports:
        intervals_by_video[video_id].extend(intervals or [])

    durations = dict(
        Video.objects.filter(videoId__in=video_ids).values_list('videoId', 'duration')
    )

    payload = []
    for a in assignments:
        key = report_key(a)
        segments = _merge_intervals(intervals_by_video.get(key))
        watched = sum(end - start for start, end in segments)
        duration = durations.get(key) or 0
        payload.append({
            'id': a.id,
            'video_id': a.video_id,
            'origin_video_id': a.origin_video_id,
            'video_type': a.video_type,
            'status': a.status,
            'created_at': a.created_at,
            'delivered_at': a.delivered_at,
            'seen_at': a.seen_at,
            'watched_seconds': round(watched, 2),
            # The watched stretches themselves, so the row can draw the same
            # segmented bar the report screen does.
            'intervals': segments,
            # None when the duration is not known yet, which is different from
            # 0% - the app draws no bar at all rather than an empty one that
            # would read as "watched nothing".
            'duration': duration or None,
            'percent': round(min(100.0, watched / duration * 100), 1) if duration else None,
        })

    return Response({'assignments': payload}, status=200)


@api_view(['GET'])
def get_mentee_progress_for_videos(request):
    """
    How much of each named video a mentee has watched.

    Exists for the case an assignment cannot answer: a mentor assigns a
    playlist or a Drive folder, and the row that records it holds the
    container's id. Which videos are inside is known only to the app, from the
    YouTube API or a folder listing - the server has never seen that list. So
    the app opens the container, and asks about the children by id.

    Deliberately not scoped to assignments: the question "how much of these has
    this mentee watched" is the useful one, and a child of an assigned playlist
    has no assignment row of its own to look up.
    """
    mentor_id = request.query_params.get('mentor_id')
    mentee_id = request.query_params.get('mentee_id')
    raw_ids = request.query_params.get('video_ids') or ''

    if not mentor_id or not mentee_id:
        return Response({'error': 'mentor_id and mentee_id are required.'}, status=400)

    video_ids = [v for v in (i.strip() for i in raw_ids.split(',')) if v]
    if not video_ids:
        return Response({'progress': []}, status=200)

    # Watch history is the mentee's own; only someone mentoring them may read
    # it. The same check get_mentee_assignments_for_mentor makes.
    if not Mentorship.objects.filter(mentor_id=mentor_id, mentee_id=mentee_id).exists():
        return Response({'error': 'No mentorship between these users.'}, status=403)

    # Capped rather than trusting the caller: this arrives straight from a
    # folder listing, and a large one would otherwise become a single enormous
    # IN clause.
    video_ids = video_ids[:300]

    reports = VideoWatchReport.objects.filter(
        user_id=mentee_id, video_id__in=video_ids
    ).values_list('video_id', 'watchedIntervals')

    intervals_by_video = defaultdict(list)
    for video_id, intervals in reports:
        intervals_by_video[video_id].extend(intervals or [])

    durations = dict(
        Video.objects.filter(videoId__in=video_ids).values_list('videoId', 'duration')
    )

    progress = []
    for video_id in video_ids:
        segments = _merge_intervals(intervals_by_video.get(video_id))
        watched = sum(end - start for start, end in segments)
        duration = durations.get(video_id) or 0
        progress.append({
            'video_id': video_id,
            'intervals': segments,
            'watched_seconds': round(watched, 2),
            'duration': duration or None,
            'percent': round(min(100.0, watched / duration * 100), 1) if duration else None,
        })

    return Response({'progress': progress}, status=200)


@api_view(['POST'])
def mark_assignments_seen(request):
    """
    The mentee opened this mentor, so everything that mentor sent has now
    actually been looked at.

    Distinct from acknowledge_assignments, which is the device reporting that
    it built the items. That happens in a background sync the mentee may never
    notice; this is a person choosing to look, which is what the mentor's blue
    tick claims.

    Only 'delivered' rows move. A 'pending' one has not been built yet, so
    opening the mentor cannot have shown it - it stays pending and is handed
    out again on the next fetch.
    """
    mentee_id = request.data.get('mentee_id')
    mentor_id = request.data.get('mentor_id')

    if not mentee_id or not mentor_id:
        return Response({'error': 'mentee_id and mentor_id are required.'}, status=400)

    updated = AssignedVideo.objects.filter(
        mentorship__mentee_id=mentee_id,
        mentorship__mentor_id=mentor_id,
        status='delivered',
    ).update(status='seen', seen_at=timezone.now())

    return Response({'seen': updated}, status=200)
