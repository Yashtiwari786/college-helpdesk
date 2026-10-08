from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib import admin
from django.urls import include, path


def home(request):
    return redirect("dashboard:dashboard")


urlpatterns = [

    path(
        "admin/",
        admin.site.urls,
    ),
    path(
        "",
        lambda request: redirect("accounts:register"),
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