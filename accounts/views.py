from django.contrib.auth import login
from django.shortcuts import render, redirect
from datetime import datetime, timedelta
from .forms import StudentRegistrationForm


def register(request):

    if request.user.is_authenticated:
        return redirect("dashboard:dashboard")

    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()

            # Automatically log the newly registered student in
            login(request, user)

            return redirect("dashboard:dashboard")

    else:
        form = StudentRegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )

import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import EmailMultiAlternatives

from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.contrib.auth import logout
from helpdesk.models import Department
from .forms import StudentRegistrationForm, StudentProfileForm


User = get_user_model()

OTP_SESSION_KEY = "registration_otp"
PENDING_USER_KEY = "pending_student_registration"
OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 5


def _send_registration_otp(request, email, first_name):
    """Generate a fresh OTP and send the branded HTML email."""
    otp = f"{secrets.randbelow(1_000_000):06d}"

    request.session[OTP_SESSION_KEY] = {
        "hash": make_password(otp),
        "expires_at": (
            timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
        ).isoformat(),
        "attempts": 0,
    }

    context = {
        "first_name": first_name,
        "otp": otp,
        "expiry_minutes": OTP_EXPIRY_MINUTES,
    }

    html_message = render_to_string(
        "emails/registration_otp.html",
        context,
    )

    email_message = EmailMultiAlternatives(
        subject="Your College Help Desk verification code",
        body=(
            f"Hello {first_name}, your verification code is {otp}. "
            f"It expires in {OTP_EXPIRY_MINUTES} minutes."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )
    email_message.attach_alternative(html_message, "text/html")
    email_message.send(fail_silently=False)


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard:dashboard")

    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)

        if form.is_valid():
            # Hash the password without creating the account yet.
            user = form.save(commit=False)

            request.session[PENDING_USER_KEY] = {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "email": user.email,
                "phone": user.phone,
                "password": user.password,
                "department": user.department_id,
                "role": User.Roles.STUDENT,
            }

            try:
                _send_registration_otp(
                    request,
                    user.email,
                    user.first_name,
                )
            except Exception:
                request.session.pop(PENDING_USER_KEY, None)
                request.session.pop(OTP_SESSION_KEY, None)
                form.add_error(
                    None,
                    "We couldn't send the verification email. "
                    "Please check your email settings and try again.",
                )
            else:
                request.session.modified = True
                return redirect("accounts:verify_email")

    else:
        form = StudentRegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form},
    )



def verify_email(request):
    pending = request.session.get(PENDING_USER_KEY)
    otp_data = request.session.get(OTP_SESSION_KEY)

    if not pending or not otp_data:
        messages.error(
            request,
            "Your verification session has expired. Please register again.",
        )
        return redirect("accounts:register")

    if request.method == "POST":

        # Resend OTP
        if request.POST.get("action") == "resend":
            try:
                _send_registration_otp(
                    request,
                    pending["email"],
                    pending["first_name"],
                )
            except Exception:
                messages.error(
                    request,
                    "We couldn't send a new code. Please try again.",
                )
            else:
                messages.success(
                    request,
                    "A new verification code was sent.",
                )

            return redirect("accounts:verify_email")

        # Validate OTP
        otp = request.POST.get("otp", "").strip()
        otp_data = request.session.get(OTP_SESSION_KEY, {})

        expiry = (
            datetime.fromisoformat(otp_data["expires_at"])
            if otp_data.get("expires_at")
            else None
        )

        if expiry is None or timezone.now() >= expiry:
            request.session.pop(OTP_SESSION_KEY, None)
            messages.error(
                request,
                "Your code has expired. Request a new code below.",
            )
            return render(
                request,
                "accounts/verify_email.html",
                {"email": pending["email"]},
            )

        # Limit incorrect attempts
        attempts = otp_data.get("attempts", 0)

        if attempts >= MAX_OTP_ATTEMPTS:
            request.session.pop(OTP_SESSION_KEY, None)
            messages.error(
                request,
                "Too many incorrect attempts. Request a new code.",
            )
            return render(
                request,
                "accounts/verify_email.html",
                {"email": pending["email"]},
            )

        # Check OTP
        if (
            len(otp) != 6
            or not otp.isdigit()
            or not check_password(otp, otp_data["hash"])
        ):
            otp_data["attempts"] = attempts + 1
            request.session[OTP_SESSION_KEY] = otp_data
            request.session.modified = True

            messages.error(
                request,
                "That code is incorrect. Please try again.",
            )
            return render(
                request,
                "accounts/verify_email.html",
                {"email": pending["email"]},
            )

        # Check username uniqueness
        if User.objects.filter(
            username=pending["username"]
        ).exists():
            messages.error(
                request,
                "That student ID is already registered. Please log in.",
            )
            request.session.pop(PENDING_USER_KEY, None)
            request.session.pop(OTP_SESSION_KEY, None)
            return redirect("accounts:login")

        # Check email uniqueness
        if User.objects.filter(
            email__iexact=pending["email"]
        ).exists():
            messages.error(
                request,
                "That email is already registered. Please log in.",
            )
            request.session.pop(PENDING_USER_KEY, None)
            request.session.pop(OTP_SESSION_KEY, None)
            return redirect("accounts:login")

        # Get the selected active department
        department = Department.objects.filter(
            pk=pending.get("department"),
            is_active=True,
        ).first()

        if department is None:
            request.session.pop(PENDING_USER_KEY, None)
            request.session.pop(OTP_SESSION_KEY, None)

            messages.error(
                request,
                "The selected department is unavailable. Please register again.",
            )
            return redirect("accounts:register")

        # Create the student account
        user = User(
            first_name=pending["first_name"],
            last_name=pending["last_name"],
            username=pending["username"],
            email=pending["email"],
            phone=pending.get("phone", ""),
            department=department,
            role=User.Roles.STUDENT,
            password=pending["password"],
        )
        user.save()

        # Clear verification session
        request.session.pop(PENDING_USER_KEY, None)
        request.session.pop(OTP_SESSION_KEY, None)

        # Log in the verified student
        login(request, user)

        messages.success(
            request,
            "Email verified! Your account is ready.",
        )

        return redirect("dashboard:dashboard")

    return render(
        request,
        "accounts/verify_email.html",
        {"email": pending["email"]},
    )


@login_required
def profile(request):
    if request.user.role != User.Roles.STUDENT:
        messages.error(request, "This page is for student accounts only.")
        return redirect("dashboard:dashboard")

    return render(
        request,
        "accounts/profile.html",
        {"profile_user": request.user},
    )


@login_required
def edit_profile(request):
    if request.user.role != User.Roles.STUDENT:
        messages.error(request, "This page is for student accounts only.")
        return redirect("dashboard:dashboard")

    if request.method == "POST":
        form = StudentProfileForm(
            request.POST,
            instance=request.user,
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Your profile was updated successfully.")
            return redirect("accounts:profile")
    else:
        form = StudentProfileForm(instance=request.user)

    return render(
        request,
        "accounts/edit_profile.html",
        {"form": form},
    )