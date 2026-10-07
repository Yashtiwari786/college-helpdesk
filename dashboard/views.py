from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect


@login_required
def dashboard(request):

    user = request.user

    if user.role == user.Roles.STUDENT:
        return render(
            request,
            "dashboard/dashboard.html",
            {
                "dashboard_type": "student",
                "title": "Student Dashboard",
            }
        )

    if user.role == user.Roles.STAFF:
        return render(
            request,
            "dashboard/dashboard.html",
            {
                "dashboard_type": "staff",
                "title": "Staff Dashboard",
            }
        )

    if user.role == user.Roles.ADMIN:
        return render(
            request,
            "dashboard/dashboard.html",
            {
                "dashboard_type": "admin",
                "title": "Admin Dashboard",
            }
        )

    return redirect("/accounts/login/")