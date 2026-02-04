from django.urls import path
from .views import *

urlpatterns = [
    path('assign_videos_to_mentees/', assign_videos_to_mentees),
      path('assignments-for-mentee/', get_assignments_for_mentee),
      path('assignments-count-for-mentee/', get_pending_assignments_count_for_mentee),
]