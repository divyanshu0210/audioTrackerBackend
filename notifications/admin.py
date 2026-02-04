from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'type',
        'status',
        'sender_id',
        'sender_name',
        'receiver_id',
        'receiver_name',
        'created_at',
    )
    list_filter = ('type', 'status', 'created_at')
    search_fields = ('sender_name', 'receiver_name', 'type')
    ordering = ('-created_at',)
