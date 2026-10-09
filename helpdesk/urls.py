from django.urls import path
from . import views


app_name = "helpdesk"


urlpatterns = [

    # Student
    path(
        "requests/",
        views.student_requests,
        name="requests"
    ),

    path(
        "requests/new/",
        views.create_request,
        name="create_request"
    ),

    path(
        "requests/<str:ticket_number>/",
        views.request_detail,
        name="request_detail"
    ),

    path(
        "requests/<str:ticket_number>/message/",
        views.send_message,
        name="send_message"
    ),

    path(
        "requests/<str:ticket_number>/feedback/",
        views.submit_feedback,
        name="submit_feedback"
    ),

    # Staff
    path(
        "staff/",
        views.staff_dashboard,
        name="staff_dashboard"
    ),

    path(
        "staff/requests/",
        views.staff_requests,
        name="staff_requests"
    ),

    path(
        "staff/requests/<str:ticket_number>/",
        views.staff_request_detail,
        name="staff_request_detail"
    ),

    path(
        "staff/requests/<str:ticket_number>/update/",
        views.staff_update_request,
        name="staff_update_request"
    ),

    path(
        "staff/requests/<str:ticket_number>/message/",
        views.staff_send_message,
        name="staff_send_message"
    ),

    # Admin
path(
    "admin-panel/",
    views.admin_dashboard,
    name="admin_dashboard"
),

path(
    "admin-panel/students/",
    views.admin_students,
    name="admin_students"
),

path(
    "admin-panel/staff/",
    views.admin_staff,
    name="admin_staff"
),

path(
    "admin-panel/staff/add/",
    views.admin_add_staff,
    name="admin_add_staff"
),

path(
    "admin-panel/requests/",
    views.admin_requests,
    name="admin_requests"
),

path(
    "admin-panel/requests/<str:ticket_number>/assign/",
    views.admin_assign_request,
    name="admin_assign_request"
),

path(
    "admin-panel/departments/",
    views.admin_departments,
    name="admin_departments"
),


# Department management
path(
    "admin-panel/departments/add/",
    views.admin_add_department,
    name="admin_add_department",
),
path(
    "admin-panel/departments/<int:department_id>/edit/",
    views.admin_edit_department,
    name="admin_edit_department",
),

# Category management
path(
    "admin-panel/categories/",
    views.admin_categories,
    name="admin_categories",
),
path(
    "admin-panel/categories/add/",
    views.admin_add_category,
    name="admin_add_category",
),
path(
    "admin-panel/categories/<int:category_id>/edit/",
    views.admin_edit_category,
    name="admin_edit_category",
),
]