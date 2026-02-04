from django.contrib import admin
from .models import AssignedVideo

@admin.register(AssignedVideo)
class AssignedVideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'video_type', 'video_id', 'mentorship','status', 'created_at')
    list_filter = ('video_type', 'created_at')
    search_fields = ('video_id', 'mentorship__mentor__email', 'mentorship__mentee__email')