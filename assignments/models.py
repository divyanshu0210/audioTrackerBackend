from django.db import models
from mentor_mentee.models import Mentorship

class AssignedVideo(models.Model):
    VIDEO_TYPE_CHOICES = [
        ('youtube', 'YouTube'),
        ('file', 'File'),
        ('device', 'Device'),
        ('drive', 'Drive'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
    ]

    mentorship = models.ForeignKey(Mentorship, on_delete=models.CASCADE, related_name='assigned_videos')
    video_id = models.CharField(max_length=255)
    video_type = models.CharField(max_length=10, choices=VIDEO_TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('mentorship', 'video_id', 'video_type')

    def __str__(self):
        return f"{self.video_type} video {self.video_id} assigned to {self.mentorship.mentee.full_name} by {self.mentorship.mentor.full_name}"
