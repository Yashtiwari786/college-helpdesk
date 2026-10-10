from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from . import views


app_name = "accounts"


urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html"
        ),
        name="login",
    ),

    path(
        "register/",
        views.register,
        name="register",
    ),

    path(
        "logout/",
        LogoutView.as_view(next_page="accounts:login"),
        name="logout",
    ),

    path(
    "verify-email/",
    views.verify_email,
    name="verify_email",
),

]