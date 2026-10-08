from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model

from helpdesk.models import Request


User = get_user_model()


@login_required
def dashboard(request):

    user = request.user

    # =========================
    # STUDENT DASHBOARD
    # =========================
    if user.role == user.Roles.STUDENT:

        student_requests = Request.objects.filter(
            student=user
        )

        total_requests = student_requests.count()

        pending_requests = student_requests.filter(
            status=Request.Status.PENDING
        ).count()

        in_progress_requests = student_requests.filter(
            status=Request.Status.IN_PROGRESS
        ).count()

        resolved_requests = student_requests.filter(
            status__in=[
                Request.Status.RESOLVED,
                Request.Status.CLOSED,
            ]
        ).count()

        recent_requests = (
            student_requests
            .select_related(
                "department",
                "category",
            )
            .order_by("-created_at")[:5]
        )

        return render(
            request,
            "dashboard/dashboard.html",
            {
                "dashboard_type": "student",
                "title": "Student Dashboard",

                "total_requests": total_requests,
                "pending_requests": pending_requests,
                "in_progress_requests": in_progress_requests,
                "resolved_requests": resolved_requests,

                "recent_requests": recent_requests,
            }
        )

    # =========================
    # STAFF DASHBOARD
    # =========================
    if user.role == user.Roles.STAFF:

        assigned_requests = Request.objects.filter(
            assigned_staff=user
        )

        pending_requests = assigned_requests.filter(
            status=Request.Status.PENDING
        ).count()

        in_progress_requests = assigned_requests.filter(
            status=Request.Status.IN_PROGRESS
        ).count()

        resolved_requests = assigned_requests.filter(
            status__in=[
                Request.Status.RESOLVED,
                Request.Status.CLOSED,
            ]
        ).count()

        recent_requests = (
            assigned_requests
            .select_related(
                "student",
                "department",
                "category",
            )
            .order_by("-created_at")[:5]
        )

        return render(
            request,
            "dashboard/dashboard.html",
            {
                "dashboard_type": "staff",
                "title": "Staff Dashboard",

                "assigned_requests": assigned_requests.count(),
                "pending_requests": pending_requests,
                "in_progress_requests": in_progress_requests,
                "resolved_requests": resolved_requests,

                "recent_requests": recent_requests,
            }
        )

    # =========================
    # ADMIN
    # =========================
    if user.role == user.Roles.ADMIN:

        return redirect("dashboard:admin_dashboard")

    # =========================
    # UNKNOWN ROLE
    # =========================

    return redirect("accounts:login")


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@login_required
def admin_dashboard(request):

    user = request.user

    # Only ADMIN can access this page
    if user.role != user.Roles.ADMIN:
        return redirect("dashboard:dashboard")

    total_students = User.objects.filter(
        role=user.Roles.STUDENT
    ).count()

    total_staff = User.objects.filter(
        role=user.Roles.STAFF
    ).count()

    total_requests = Request.objects.count()

    pending_requests = Request.objects.filter(
        status=Request.Status.PENDING
    ).count()

    in_progress_requests = Request.objects.filter(
        status=Request.Status.IN_PROGRESS
    ).count()

    resolved_requests = Request.objects.filter(
        status__in=[
            Request.Status.RESOLVED,
            Request.Status.CLOSED,
        ]
    ).count()

    recent_requests = (
        Request.objects
        .select_related(
            "student",
            "department",
            "category",
            "assigned_staff",
        )
        .order_by("-created_at")[:10]
    )

    return render(
        request,
        "admin_panel/dashboard.html",
        {
            "dashboard_type": "admin",
            "title": "Admin Dashboard",

            "total_students": total_students,
            "total_staff": total_staff,
            "total_requests": total_requests,

            "pending_requests": pending_requests,
            "in_progress_requests": in_progress_requests,
            "resolved_requests": resolved_requests,

            "recent_requests": recent_requests,
        }
    )