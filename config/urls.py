from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib import admin
from django.urls import include, path
from config.views import landing_page
from helpdesk import views as helpdesk_views



urlpatterns = [

    path(
        "admin/",
        admin.site.urls,
    ),
    path(
        "",
        landing_page,
        name="home",
    ),

    path(
        "accounts/",
        include("accounts.urls"),
    ),

    path(
        "dashboard/",
        include("dashboard.urls"),
    ),

    path(
        "helpdesk/",
        include("helpdesk.urls"),
    ),
    path(
        "faculty/",
        helpdesk_views.faculty_directory,
        name="faculty_directory",
    ),
]


if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )