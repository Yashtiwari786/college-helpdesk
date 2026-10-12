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
    path(
        "department-students/",
        views.department_students,
        name="department_students",
    ),
    path(
        "department-staff/",
        views.department_staff,
        name="department_staff",
    ),

    path("admin/students/", views.student_list, name="student_list"),
    path("admin/students/create/", views.student_create, name="student_create"),
    path(
        "admin/students/<int:student_id>/edit/",
        views.student_edit,
        name="student_edit",
    ),
    path(
        "admin/students/<int:student_id>/delete/",
        views.student_delete,
        name="student_delete",
    ),
]