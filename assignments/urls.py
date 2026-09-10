from django.urls import path
from .views import *

urlpatterns = [
    path('assign_videos_to_mentees/', assign_videos_to_mentees),
      path('assignments-for-mentee/', get_assignments_for_mentee),
      path('assignments-count-for-mentee/', get_pending_assignments_count_for_mentee),
      path('acknowledge/', acknowledge_assignments),
      path('mark-seen/', mark_assignments_seen),
      path('mentee-assignments/', get_mentee_assignments_for_mentor),
      path('mentee-progress/', get_mentee_progress_for_videos),
]