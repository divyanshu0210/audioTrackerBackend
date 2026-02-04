from django.urls import path
from .views import *

urlpatterns = [
    path('register_device_token/', register_device_token),
  
]
