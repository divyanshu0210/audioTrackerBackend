
from rest_framework import serializers
from .models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'



class MentorshipRequestSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)

    class Meta:
        model = MentorshipRequest
        fields = ['id', 'sender', 'receiver', 'status', 'type','created_at']


# class MentorGroupSerializer(serializers.ModelSerializer):
#     mentor = UserSerializer(read_only=True)  # Show mentor details in response
#     mentor_id = serializers.PrimaryKeyRelatedField(
#         queryset=User.objects.all(), source="mentor", write_only=True
#     )  # Accept mentor ID while creating/updating

#     class Meta:
#         model = MentorGroup
#         fields = ["id", "name", "mentor", "mentor_id"]
#         extra_kwargs = {
#             "name": {"required": True}
#         }

# class GroupWithMenteesSerializer(serializers.ModelSerializer):
#     mentor = UserSerializer(read_only=True)
#     mentees = serializers.SerializerMethodField()

#     class Meta:
#         model = MentorGroup
#         fields = ["id", "name", "mentor", "mentees"]

#     def get_mentees(self, obj):
#         memberships = obj.memberships.all()
#         return [UserSerializer(m.mentee).data for m in memberships]



# class GroupMembershipSerializer(serializers.ModelSerializer):
#     group = MentorGroupSerializer(read_only=True)
#     group_id = serializers.PrimaryKeyRelatedField(
#         queryset=MentorGroup.objects.all(), source="group", write_only=True
#     )

#     mentee = UserSerializer(read_only=True)
#     mentee_id = serializers.PrimaryKeyRelatedField(
#         queryset=User.objects.all(), source="mentee", write_only=True
#     )

#     class Meta:
#         model = GroupMembership
#         fields = ["id", "group", "group_id", "mentee", "mentee_id"]
#         extra_kwargs = {
#             "group_id": {"required": True},
#             "mentee_id": {"required": True},
#         }

# # Simple group list serializer (no mentees)
# class MentorGroupListSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = MentorGroup
#         fields = ["id", "name"]
        

# # Detailed group serializer (with mentees)
# class GroupDetailSerializer(serializers.ModelSerializer):
#     mentor = UserSerializer(read_only=True)
#     mentees = serializers.SerializerMethodField()

#     class Meta:
#         model = MentorGroup
#         fields = ["id", "name", "mentor", "mentees"]

#     def get_mentees(self, obj):
#         memberships = obj.memberships.all()
#         return [UserSerializer(m.mentee).data for m in memberships]

