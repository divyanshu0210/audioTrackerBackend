from django.contrib import admin
from .models import Video, VideoWatchReport

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Video._meta.fields]
    search_fields = ('videoId', 'name')
    list_filter = ('type',)

@admin.register(VideoWatchReport)
class VideoWatchReportAdmin(admin.ModelAdmin):
    list_display = [field.name for field in VideoWatchReport._meta.fields]
    search_fields = ('user__email', 'video__videoId')  # Adjust depending on your User model
    list_filter = ('date',)
