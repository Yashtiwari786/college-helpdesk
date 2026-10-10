
from django.shortcuts import render
from helpdesk.models import Department, StaffProfile


def landing_page(request):
    departments = Department.objects.filter(
        is_active=True
    ).order_by("name")

    staff_profiles = (
        StaffProfile.objects
        .filter(
            user__role="STAFF",
            user__is_active=True,
            department__is_active=True,
        )
        .select_related("user", "department")
        .order_by("department__name", "designation", "user__username")
    )

    designations = (
        StaffProfile.objects
        .filter(
            user__role="STAFF",
            user__is_active=True,
            department__is_active=True,
        )
        .exclude(designation="")
        .values_list("designation", flat=True)
        .distinct()
        .order_by("designation")
    )

    return render(
        request,
        "landing.html",
        {
            "departments": departments,
            "staff_profiles": staff_profiles,
            "designations": designations,
        },
    )
