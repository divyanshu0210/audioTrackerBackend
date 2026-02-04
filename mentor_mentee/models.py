from django.db import models

# Create your models here.

class User(models.Model):
    id = models.CharField(primary_key=True, max_length=100, unique=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)

    def __str__(self):
        return self.full_name

# ----------------------------------------------------------

# class MentorGroup(models.Model):
#     name = models.CharField(max_length=255)
#     mentor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mentor_groups")

#     class Meta:
#         unique_together = ("mentor", "name")  # Mentor cannot have duplicate group names

#     def __str__(self):
#         return f"{self.name} (Mentor: {self.mentor.full_name})"


# class GroupMembership(models.Model):
#     group = models.ForeignKey(MentorGroup, on_delete=models.CASCADE, related_name="memberships")
#     mentee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="group_memberships")

#     class Meta:
#         unique_together = ("group", "mentee")  # Prevent duplicate memberships

#     def __str__(self):
#         return f"{self.mentee.full_name} in {self.group.name}"
    

# ----------------------------------------------------------

class MentorshipRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    TYPE_CHOICES = [
        ('mentor', 'Mentor'),
        ('mentee', 'Mentee'),
    ]

    sender = models.ForeignKey('User', on_delete=models.CASCADE, related_name='sent_requests')
    receiver = models.ForeignKey('User', on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES,default='mentee')  # New field
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'receiver')  # Prevent duplicate requests

    def __str__(self):
        return f"{self.sender.full_name} → {self.receiver.full_name} ({self.status}) as {self.type}"


class Mentorship(models.Model):
    mentor = models.ForeignKey('User', on_delete=models.CASCADE, related_name='mentees')
    mentee = models.ForeignKey('User', on_delete=models.CASCADE, related_name='mentors')
    started_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('mentor', 'mentee')

    def __str__(self):
        return f"{self.mentee.full_name} is mentored by {self.mentor.full_name}"

