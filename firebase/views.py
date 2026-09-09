from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import DeviceToken
from mentor_mentee.models import *

@api_view(['POST'])
def register_device_token(request):
    token = request.data.get("token")
    user_id = request.data.get("user_id")   # 👈 pass from frontend

    if not token:
        return Response({"error": "Token is required"}, status=400)

    if not user_id :
        return Response({"error": "Either user_id or email is required"}, status=400)

    try:
        if user_id:
            user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    # `token` is the unique column, so it has to be the lookup key and the user
    # has to be a default. Looking up on (user, token) meant that re-registering
    # a device under a second account found no row, tried to INSERT, and hit the
    # unique constraint on `token` — a 500 that the app used to swallow, leaving
    # the account with no reachable device. Keying on the token instead simply
    # moves the device to whoever logged in last, which is what actually happened.
    DeviceToken.objects.update_or_create(token=token, defaults={"user": user})
    return Response({"message": "Token registered successfully"})
