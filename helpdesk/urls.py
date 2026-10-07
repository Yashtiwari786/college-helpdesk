from django.urls import path

from . import views


app_name = "helpdesk"


urlpatterns = [

    path(
        "requests/",
        views.student_requests,
        name="requests",
    ),

    path(
        "requests/new/",
        views.create_request,
        name="create_request",
    ),

    path(
        "requests/<str:ticket_number>/",
        views.request_detail,
        name="request_detail",
    ),

    path(
        "requests/<str:ticket_number>/message/",
        views.send_message,
        name="send_message",
    ),

    path(
        "requests/<str:ticket_number>/feedback/",
        views.submit_feedback,
        name="submit_feedback",
    ),
]