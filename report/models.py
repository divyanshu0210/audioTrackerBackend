from django.db import models
from django.utils import timezone
import datetime
from mentor_mentee.models import User

VIDEO_TYPES = [
    ('drive', 'Drive'),
    ('device', 'Device'),
    ('youtube', 'YouTube'),
]

class Video(models.Model):
    id = models.AutoField(primary_key=True)
    videoId = models.CharField(max_length=255, unique=True)
    name = models.TextField()
    duration = models.IntegerField(default=0)
    type = models.CharField(max_length=10, choices=VIDEO_TYPES)
    mimetype = models.TextField()

    def __str__(self):
        return f"{self.name} ({self.type})"


class VideoWatchReport(models.Model):
    id = models.AutoField(primary_key=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, to_field='id', db_column='userId')
    video = models.ForeignKey('Video', on_delete=models.CASCADE, to_field='videoId', db_column='videoId')

    watchedIntervals = models.JSONField()
    todayIntervals = models.JSONField()

    date = models.DateField(default=datetime.date.today)  # Format: YYYY-MM-DD
    lastWatchedAt = models.DateTimeField(default=timezone.now)  # Full timestamp

    lastWatchTime = models.IntegerField(default=0)
    watchTimePerDay = models.IntegerField(default=0)
    newWatchTimePerDay = models.IntegerField(default=0)
    unfltrdWatchTimePerDay = models.IntegerField(default=0)

    class Meta:
        unique_together = ('user', 'video', 'date')

    def __str__(self):
        return f"{self.user_id} - {self.video_id} - {self.date}"
