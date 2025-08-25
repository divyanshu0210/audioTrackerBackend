from django.contrib import admin
from .models import User, MentorshipRequest, Mentorship

# admin.site.register(User)
# admin.site.register(MentorshipRequest)
# admin.site.register(Mentorship)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'full_name')
    search_fields = ('email', 'full_name')


@admin.register(MentorshipRequest)
class MentorshipRequestAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'status','type', 'created_at')
    list_filter = ('status',)
    search_fields = ('sender__full_name', 'receiver__full_name')


@admin.register(Mentorship)
class MentorshipAdmin(admin.ModelAdmin):
    list_display = ('mentor', 'mentee', 'started_at')
    search_fields = ('mentor__full_name', 'mentee__full_name')
