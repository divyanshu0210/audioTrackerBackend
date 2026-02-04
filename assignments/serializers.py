from rest_framework import serializers
from .models import AssignedVideo

class AssignedVideoSerializer(serializers.ModelSerializer):
    mentee_id = serializers.SerializerMethodField()
    mentor_id = serializers.SerializerMethodField()
    mentee_email = serializers.SerializerMethodField()
    mentor_email = serializers.SerializerMethodField()

    class Meta:
        model = AssignedVideo
        fields = [
            'id',
            'mentee_id',
            'mentor_id',
            'mentee_email',
            'mentor_email',
            'video_id',
            'video_type',
            'created_at'
        ]

    def get_mentee_id(self, obj):
        return obj.mentorship.mentee.id

    def get_mentor_id(self, obj):
        return obj.mentorship.mentor.id

    def get_mentee_email(self, obj):
        return obj.mentorship.mentee.email

    def get_mentor_email(self, obj):
        return obj.mentorship.mentor.email
