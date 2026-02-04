from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Video, VideoWatchReport
from mentor_mentee.models import User
from django.utils.dateparse import parse_datetime
from django.db import IntegrityError
from django.db.models import Sum


@api_view(['POST'])
def upload_video_report(request):
    data = request.data

    # Extract video and report parts
    video_data = data.get('video')
    report_data = data.get('report')

    if not video_data or not report_data:
        return Response({'error': 'Missing video or report data'}, status=status.HTTP_400_BAD_REQUEST)

    # Create or get the Video object
    video_obj, _ = Video.objects.get_or_create(
        videoId=video_data['videoId'],
        defaults={
            'name': video_data['name'],
            'duration': int(video_data['duration']),
            'type': video_data['type'],
            'mimetype': video_data['mimetype'],
        }
    )

    # Make sure the user exists
    try:
        user_obj = User.objects.get(id=report_data['user'])
    except User.DoesNotExist:
        return Response({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)

    # Prepare data for VideoWatchReport
    try:
        report_obj, created = VideoWatchReport.objects.update_or_create(
            user=user_obj,
            video=video_obj,
            date=report_data['date'],
            defaults={
                'watchedIntervals': report_data['watchedIntervals'],
                'todayIntervals': report_data['todayIntervals'],
                'lastWatchedAt': parse_datetime(report_data['lastWatchedAt']),
                'lastWatchTime': int(report_data['lastWatchTime']),
                'watchTimePerDay': int(report_data['watchTimePerDay']),
                'newWatchTimePerDay': int(report_data['newWatchTimePerDay']),
                'unfltrdWatchTimePerDay': int(report_data['unfltrdWatchTimePerDay']),
            }
        )
    except IntegrityError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'message': 'Video report saved successfully',
        'videoId': video_obj.videoId,
        'user': user_obj.id,
        'date': report_data['date'],
        'created': created
    }, status=status.HTTP_201_CREATED)



@api_view(['GET'])
def monthly_watch_time_view(request):
    user_id = request.GET.get('userId')
    start_date = request.GET.get('startDate')
    end_date = request.GET.get('endDate')

    if not user_id or not start_date or not end_date:
        return Response({'error': 'Missing required parameters'}, status=status.HTTP_400_BAD_REQUEST)

    queryset = (
        VideoWatchReport.objects
        .filter(user_id=user_id, date__range=[start_date, end_date])
        .values('date')
        .annotate(
            totalWatchTime=Sum('watchTimePerDay'),
            totalNewWatchTime=Sum('newWatchTimePerDay'),
            totalUnfltrdWatchTime=Sum('unfltrdWatchTimePerDay'),
        )
        .order_by('date')
    )

    data = {
        entry['date'].isoformat(): {
            'totalWatchTime': entry['totalWatchTime'] or 0,
            'totalNewWatchTime': entry['totalNewWatchTime'] or 0,
            'totalUnfltrdWatchTime': entry['totalUnfltrdWatchTime'] or 0,
        }
        for entry in queryset
    }

    return Response(data, status=status.HTTP_200_OK)

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import VideoWatchReport
from datetime import datetime

@api_view(['GET'])
def get_watch_history_by_date(request):
    date_str = request.GET.get('date')
    user_id = request.GET.get('userId')

    if not date_str or not user_id:
        return Response({"error": "Missing 'date' or 'userId'."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return Response({"error": "Invalid date format. Expected YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

    reports = VideoWatchReport.objects.filter(user_id=user_id, date=date).select_related('video').order_by('-lastWatchedAt')

    data = [
        {
            "id": r.id,
            "userId": r.user_id,
            "videoId": r.video.videoId,
            "watchedIntervals": r.watchedIntervals,
            "todayIntervals": r.todayIntervals,
            "date": r.date.isoformat(),
            "lastWatchedAt": r.lastWatchedAt.isoformat(),
            "lastWatchTime": r.lastWatchTime,
            "watchTimePerDay": r.watchTimePerDay,
            "newWatchTimePerDay": r.newWatchTimePerDay,
            "unfltrdWatchTimePerDay": r.unfltrdWatchTimePerDay,

            "videoNameInfo": r.video.name,
            "duration": r.video.duration,
            "source_type": r.video.type,
            "mimetype": r.video.mimetype,
        }
        for r in reports
    ]

    return Response(data, status=status.HTTP_200_OK)
