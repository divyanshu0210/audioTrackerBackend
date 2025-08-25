from rest_framework import serializers
from .models import Video, VideoWatchReport
from mentor_mentee.models import User

class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = '__all__'

class VideoWatchReportSerializer(serializers.ModelSerializer):
    user = serializers.CharField()  # Just accept the string ID
    video = serializers.CharField()  # Just accept the videoId string
    
    class Meta:
        model = VideoWatchReport
        fields = '__all__'

    