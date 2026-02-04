from django.urls import path
from .views import *

urlpatterns = [
    path('upload-video-report/', upload_video_report),
    path('monthly-watch-time/', monthly_watch_time_view),
    path('watch-history-by-date', get_watch_history_by_date),
]

