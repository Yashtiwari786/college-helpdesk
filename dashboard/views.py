from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import redirect, render

from helpdesk.models import Request


@login_required
def dashboard(request):

    user = request.user


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

                "in_progress_requests":
                    in_progress_requests,

                "resolved_requests":
                    resolved_requests,

                "recent_requests":
                    recent_requests,
            }
        )


    if user.role == user.Roles.STAFF:

        assigned_requests = Request.objects.filter(
            assigned_staff=user
        )

        return render(
            request,
            "dashboard/dashboard.html",
            {
                "dashboard_type": "staff",
                "title": "Staff Dashboard",
                "assigned_requests":
                    assigned_requests.count(),
            }
        )


    if user.role == user.Roles.ADMIN:

        return render(
            request,
            "dashboard/dashboard.html",
            {
                "dashboard_type": "admin",
                "title": "Admin Dashboard",

                "total_students":
                    request.user.__class__.objects.filter(
                        role="STUDENT"
                    ).count(),

                "total_staff":
                    request.user.__class__.objects.filter(
                        role="STAFF"
                    ).count(),

                "total_requests":
                    Request.objects.count(),

                "resolved_requests":
                    Request.objects.filter(
                        status__in=[
                            Request.Status.RESOLVED,
                            Request.Status.CLOSED,
                        ]
                    ).count(),
            }
        )


    return redirect("accounts:login")