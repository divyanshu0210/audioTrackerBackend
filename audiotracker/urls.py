
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('mentor_mentee.urls')),
    path('assign/',include('assignments.urls')),
    path('report/',include('report.urls')),
    path('notifications/', include('notifications.urls')),
    path('fcm/', include('firebase.urls')),
]
