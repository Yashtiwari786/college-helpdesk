from django.urls import path
from . import views


app_name = "helpdesk"


urlpatterns = [

    # Student
    path(
        "requests/",
        views.student_requests,
        name="requests"
    ),

    path(
        "requests/new/",
        views.create_request,
        name="create_request"
    ),

    path(
        "requests/<str:ticket_number>/",
        views.request_detail,
        name="request_detail"
    ),

    path(
        "requests/<str:ticket_number>/message/",
        views.send_message,
        name="send_message"
    ),

    path(
        "requests/<str:ticket_number>/feedback/",
        views.submit_feedback,
        name="submit_feedback"
    ),

    # Staff
    path(
        "staff/",
        views.staff_dashboard,
        name="staff_dashboard"
    ),

    path(
        "staff/requests/",
        views.staff_requests,
        name="staff_requests"
    ),

    path(
        "staff/requests/<str:ticket_number>/",
        views.staff_request_detail,
        name="staff_request_detail"
    ),

    path(
        "staff/requests/<str:ticket_number>/update/",
        views.staff_update_request,
        name="staff_update_request"
    ),

    path(
        "staff/requests/<str:ticket_number>/message/",
        views.staff_send_message,
        name="staff_send_message"
    ),
]