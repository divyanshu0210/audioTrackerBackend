from django.contrib import admin
from .models import DeviceToken

@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "token", "created_at")  # columns shown in admin list
    search_fields = ("user__email", "token")       # search by user email or token
    list_filter = ("created_at",)                  # filter by date
