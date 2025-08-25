
from django.urls import path
from .views import *

urlpatterns = [
    path('user/create/', create_user),
    path('user/list/', list_users),
    path('user/check-email/', check_email),

    path('request/send/', send_mentorship_request),
    path('request/respond/', respond_mentorship_request),
    path('request/cancel/', cancel_mentorship_request),
    path('request/received/<str:user_id>/', get_received_requests),
    path('request/all/<str:user_id>/', get_mentorship_requests),
    path('mentorships/<str:user_id>/', get_mentors_and_mentees),


    # path("groups/create/", create_group, name="create_group"),
    # path("groups/add-mentee/", add_mentee_to_group, name="add_mentee_to_group"),
    # path("mentor/<str:mentor_id>/groups/", list_groups, name="list_groups"),
    # path("mentor/<str:mentor_id>/groups/with-mentees/", list_groups_with_mentees, name="list_groups_with_mentees"),
    # path("groups/<int:group_id>/", group_detail, name="group_detail"),
    # path("groups/<int:group_id>/delete/", delete_group, name="delete_group"),
    # path("groups/<int:group_id>/mentees/<str:mentee_id>/remove/", remove_mentee_from_group, name="remove_mentee_from_group"),

]


# POST /groups/create/ → create a group with at least one mentee
# POST /groups/add-mentee/ → add more mentees later
# GET /mentor/m1/groups/ → list mentor’s groups (ids & names only)
# GET /mentor/m1/groups/with-mentees/ → list mentor’s groups with mentees
# GET /groups/1/ → get one group with its mentees
# DELETE /groups/1/delete/ → delete a group
# DELETE /groups/1/mentees/u2/remove/ → remove mentee u2 from group 1
