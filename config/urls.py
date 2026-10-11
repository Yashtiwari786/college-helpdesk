from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib import admin
from django.urls import include, path
from config.views import landing_page




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
  
]


if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )