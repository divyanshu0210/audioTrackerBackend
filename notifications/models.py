from django.db import models

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('mentor', 'Mentor'),
        ('mentee', 'Mentee'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('assignment', 'Assignment'),
        ('report', 'Report'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('viewed', 'Viewed'),
    ]

    sender_id = models.CharField()
    receiver_id = models.CharField()
    sender_name = models.CharField(max_length=100, blank=True) 
    receiver_name = models.CharField(max_length=100, blank=True) 

    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type.capitalize()} from {self.sender_id} to {self.receiver_id} ({self.status})"
