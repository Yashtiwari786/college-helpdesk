from django.urls import path

from . import views


app_name = "dashboard"


urlpatterns = [
    path(
        "",
        views.dashboard,
        name="dashboard",
    ),
    path(
        "admin-panel/",
        views.admin_dashboard,
        name="admin_dashboard",
    ),
]