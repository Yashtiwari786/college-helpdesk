from django.contrib import messages
from functools import wraps
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db import models

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Q

from django.urls import reverse
from django.views.decorators.http import require_POST
from .forms import (
    FeedbackForm,
    MessageForm,
    RequestForm,
    StaffMessageForm,
    StaffRequestUpdateForm,
    DepartmentForm,
    CategoryForm,
)

from .models import Request, Attachment, Message, Notification
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from .forms import (
    FeedbackForm,
    MessageForm,
    RequestForm,
)

from .models import (
    Attachment,
    Feedback,
    Notification,
    Request,
    Department,
    Category,
    Announcement, StaffProfile
)















def student_required(view_func):

    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("accounts:login")

        if not request.user.is_student:
            messages.error(
                request,
                "You do not have permission to access this page."
            )

            return redirect("dashboard:home")

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper


@student_required
def student_requests(request):

    query = request.GET.get(
        "q",
        ""
    ).strip()

    requests = (
        Request.objects
        .filter(student=request.user)
        .select_related(
            "department",
            "category",
            "assigned_staff",
        )
    )

    if query:

        requests = requests.filter(
            Q(ticket_number__icontains=query)
            |
            Q(subject__icontains=query)
            |
            Q(description__icontains=query)
        )

    return render(
        request,
        "student/requests.html",
        {
            "requests": requests,
            "query": query,
        }
    )



import logging

logger = logging.getLogger(__name__)


@student_required
def create_request(request):
    if request.method == "POST":
        form = RequestForm(request.POST)

        if form.is_valid():
            help_request = form.save(commit=False)
            help_request.student = request.user
            help_request.save()

            # Notification for student
            Notification.objects.create(
                user=request.user,
                title="Request Created",
                message=(
                    f"Your request {help_request.ticket_number} "
                    "has been created successfully."
                ),
                notification_type=Notification.NotificationType.REQUEST,
                request=help_request,
            )

            # Save attachments without losing the created request
            files = request.FILES.getlist("attachments")
            failed_files = []

            for uploaded_file in files:
                try:
                    Attachment.objects.create(
                        request=help_request,
                        uploaded_by=request.user,
                        file=uploaded_file,
                        original_name=uploaded_file.name,
                    )
                except Exception:
                    logger.exception(
                        "Attachment upload failed for request %s, file %s",
                        help_request.ticket_number,
                        uploaded_file.name,
                    )
                    failed_files.append(uploaded_file.name)

            if failed_files:
                messages.warning(
                    request,
                    "Your request was created, but one or more attachments "
                    "could not be uploaded. Please try again or contact support."
                )
            else:
                messages.success(
                    request,
                    f"Request {help_request.ticket_number} created successfully."
                )

            return redirect(
                "helpdesk:request_detail",
                ticket_number=help_request.ticket_number,
            )

    else:
        form = RequestForm()

    return render(
        request,
        "student/create_request.html",
        {"form": form},
    )



@student_required
def request_detail(
    request,
    ticket_number
):

    help_request = get_object_or_404(
        Request.objects
        .select_related(
            "department",
            "category",
            "assigned_staff",
            "student",
        )
        .prefetch_related(
            "attachments",
            "messages__sender",
        ),
        ticket_number=ticket_number,
        student=request.user,
    )


    message_form = MessageForm()

    feedback_form = FeedbackForm()

    existing_feedback = getattr(
        help_request,
        "feedback",
        None
    )


    return render(
        request,
        "student/request_detail.html",
        {
            "help_request": help_request,
            "message_form": message_form,
            "feedback_form": feedback_form,
            "existing_feedback": existing_feedback,
        }
    )


@student_required
def send_message(
    request,
    ticket_number
):

    if request.method != "POST":
        return redirect(
            "helpdesk:request_detail",
            ticket_number=ticket_number,
        )


    help_request = get_object_or_404(
        Request,
        ticket_number=ticket_number,
        student=request.user,
    )


    form = MessageForm(
        request.POST,
        request.FILES,
    )


    if form.is_valid():

        message = form.save(
            commit=False
        )

        message.request = help_request
        message.sender = request.user

        message.save()


        # Notify assigned staff

        if help_request.assigned_staff:

            Notification.objects.create(
                user=help_request.assigned_staff,
                title="New Message",
                message=(
                    f"New message on "
                    f"{help_request.ticket_number}."
                ),
                notification_type=(
                    Notification.NotificationType.MESSAGE
                ),
                request=help_request,
            )


        messages.success(
            request,
            "Message sent successfully."
        )


    else:

        messages.error(
            request,
            "Please enter a valid message."
        )


    return redirect(
        "helpdesk:request_detail",
        ticket_number=ticket_number,
    )


@student_required
def submit_feedback(
    request,
    ticket_number
):

    if request.method != "POST":
        return redirect(
            "helpdesk:request_detail",
            ticket_number=ticket_number,
        )


    help_request = get_object_or_404(
        Request,
        ticket_number=ticket_number,
        student=request.user,
    )


    if help_request.status not in [
        Request.Status.RESOLVED,
        Request.Status.CLOSED,
    ]:

        messages.error(
            request,
            "Feedback can only be submitted after resolution."
        )

        return redirect(
            "helpdesk:request_detail",
            ticket_number=ticket_number,
        )


    if hasattr(help_request, "feedback"):

        messages.error(
            request,
            "Feedback has already been submitted."
        )

        return redirect(
            "helpdesk:request_detail",
            ticket_number=ticket_number,
        )


    form = FeedbackForm(
        request.POST
    )


    if form.is_valid():

        feedback = form.save(
            commit=False
        )

        feedback.request = help_request
        feedback.student = request.user

        feedback.save()

        messages.success(
            request,
            "Thank you for your feedback!"
        )

    return redirect(
        "helpdesk:request_detail",
        ticket_number=ticket_number,
    )

def staff_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff_member:
            messages.error(request, "You do not have staff access.")
            return redirect("dashboard")

        return view_func(request, *args, **kwargs)

    return wrapper

@staff_required
def staff_requests(request):
    requests = Request.objects.filter(
        assigned_staff=request.user
    ).select_related(
        "student",
        "department",
        "category"
    )

    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip()
    priority = request.GET.get("priority", "").strip()

    if search:
        requests = requests.filter(
            Q(ticket_number__icontains=search)
            | Q(subject__icontains=search)
            | Q(description__icontains=search)
            | Q(student__first_name__icontains=search)
            | Q(student__last_name__icontains=search)
        )

    if status:
        requests = requests.filter(status=status)

    if priority:
        requests = requests.filter(priority=priority)

    context = {
        "requests": requests,
        "search": search,
        "selected_status": status,
        "selected_priority": priority,
        "status_choices": Request.Status.choices,
        "priority_choices": Request.Priority.choices,
    }

    return render(
        request,
        "staff/requests.html",
        context
    )

@staff_required
def staff_request_detail(request, ticket_number):
    help_request = get_object_or_404(
        Request.objects.select_related(
            "student",
            "department",
            "category",
            "assigned_staff"
        ),
        ticket_number=ticket_number
    )

    messages_list = help_request.messages.select_related(
        "sender"
    ).order_by("created_at")

    attachments = help_request.attachments.select_related(
        "uploaded_by"
    ).order_by("-uploaded_at")

    update_form = StaffRequestUpdateForm(
        instance=help_request
    )

    message_form = StaffMessageForm()

    context = {
        "help_request": help_request,
        "messages_list": messages_list,
        "attachments": attachments,
        "update_form": update_form,
        "message_form": message_form,
    }

    return render(
        request,
        "staff/request_detail.html",
        context
    )

@staff_required
def staff_update_request(request, ticket_number):
    help_request = get_object_or_404(
        Request,
        ticket_number=ticket_number
    )

    if request.method != "POST":
        return redirect(
            "helpdesk:staff_request_detail",
            ticket_number=ticket_number
        )

    form = StaffRequestUpdateForm(
        request.POST,
        instance=help_request
    )

    if form.is_valid():
        old_status = help_request.status

        updated_request = form.save()

        if updated_request.status == Request.Status.IN_PROGRESS:
            if not updated_request.assigned_staff:
                updated_request.assigned_staff = request.user

            updated_request.save()

        if updated_request.status == Request.Status.RESOLVED:
            updated_request.resolved_at = timezone.now()
            updated_request.save()

        if updated_request.status == Request.Status.CLOSED:
            updated_request.closed_at = timezone.now()
            updated_request.save()

        if old_status != updated_request.status:
            Notification.objects.create(
                user=updated_request.student,
                title="Request Status Updated",
                message=(
                    f"Your request {updated_request.ticket_number} "
                    f"is now {updated_request.get_status_display()}."
                ),
                notification_type=Notification.NotificationType.REQUEST,
                request=updated_request,
            )

        messages.success(
            request,
            "Request updated successfully."
        )

    return redirect(
        "helpdesk:staff_request_detail",
        ticket_number=ticket_number
    )

@staff_required
def staff_send_message(request, ticket_number):
    help_request = get_object_or_404(
        Request,
        ticket_number=ticket_number
    )

    if request.method != "POST":
        return redirect(
            "helpdesk:staff_request_detail",
            ticket_number=ticket_number
        )

    form = StaffMessageForm(
        request.POST,
        request.FILES
    )

    if form.is_valid():
        message = form.save(commit=False)

        message.request = help_request
        message.sender = request.user
        message.save()

        Notification.objects.create(
            user=help_request.student,
            title="New Reply",
            message=(
                f"Staff replied to your request "
                f"{help_request.ticket_number}."
            ),
            notification_type=Notification.NotificationType.MESSAGE,
            request=help_request,
        )

        messages.success(
            request,
            "Reply sent successfully."
        )

    return redirect(
        "helpdesk:staff_request_detail",
        ticket_number=ticket_number
    )

@staff_required
def staff_dashboard(request):
    assigned_requests = Request.objects.filter(
        assigned_staff=request.user
    )

    total_requests = assigned_requests.count()

    pending_requests = assigned_requests.filter(
        status=Request.Status.PENDING
    ).count()

    assigned_count = assigned_requests.filter(
        status=Request.Status.ASSIGNED
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

    recent_requests = assigned_requests.select_related(
        "student",
        "department",
        "category"
    ).order_by("-created_at")[:10]

    context = {
        "total_requests": total_requests,
        "pending_requests": pending_requests,
        "assigned_count": assigned_count,
        "in_progress_requests": in_progress_requests,
        "resolved_requests": resolved_requests,
        "recent_requests": recent_requests,
    }

    return render(
        request,
        "staff/dashboard.html",
        context
    )

def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):

        if request.user.role != request.user.Roles.ADMIN:
            messages.error(
                request,
                "You do not have administrator access."
            )

            return redirect("/accounts/login/")

        return view_func(request, *args, **kwargs)

    return wrapper

@admin_required
def admin_dashboard(request):

    total_students = User.objects.filter(
        role=User.Roles.STUDENT
    ).count()

    total_staff = User.objects.filter(
        role=User.Roles.STAFF
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

    total_departments = Department.objects.filter(
        is_active=True
    ).count()

    total_categories = Category.objects.filter(
        is_active=True
    ).count()

    recent_requests = Request.objects.select_related(
        "student",
        "department",
        "category",
        "assigned_staff",
    ).order_by("-created_at")[:10]

    recent_announcements = Announcement.objects.filter(
        is_active=True
    ).order_by("-created_at")[:5]

    context = {
        "total_students": total_students,
        "total_staff": total_staff,
        "total_requests": total_requests,
        "pending_requests": pending_requests,
        "in_progress_requests": in_progress_requests,
        "resolved_requests": resolved_requests,
        "total_departments": total_departments,
        "total_categories": total_categories,
        "recent_requests": recent_requests,
        "recent_announcements": recent_announcements,
    }

    return render(
        request,
        "admin_panel/dashboard.html",
        context
    )

@admin_required
def admin_students(request):

    students = User.objects.filter(
        role=User.Roles.STUDENT
    ).order_by(
        "-date_joined"
    )

    search = request.GET.get("search", "").strip()

    if search:
        students = students.filter(
            Q(username__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(email__icontains=search)
        )

    return render(
        request,
        "admin_panel/students.html",
        {
            "students": students,
            "search": search,
        }
    )


@admin_required
def admin_staff(request):
    staff_members = (
        User.objects
        .filter(role=User.Roles.STAFF)
        .select_related("staff_profile__department")
        .order_by("-date_joined")
    )

    search = request.GET.get("search", "").strip()
    department_id = request.GET.get("department", "").strip()

    if search:
        staff_members = staff_members.filter(
            Q(username__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(email__icontains=search)
            | Q(phone__icontains=search)
        )

    if department_id.isdigit():
        staff_members = staff_members.filter(
            staff_profile__department_id=int(department_id)
        )

    departments = Department.objects.filter(
        is_active=True
    ).order_by("name")

    return render(
        request,
        "admin_panel/staff.html",
        {
            "staff_members": staff_members,
            "search": search,
            "departments": departments,
            "selected_department": department_id,
        },
    )
@admin_required
def admin_requests(request):

    requests = Request.objects.select_related(
        "student",
        "department",
        "category",
        "assigned_staff",
    ).order_by("-created_at")

    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip()
    department = request.GET.get("department", "").strip()

    if search:
        requests = requests.filter(
            Q(ticket_number__icontains=search)
            | Q(subject__icontains=search)
            | Q(student__username__icontains=search)
        )

    if status:
        requests = requests.filter(
            status=status
        )

    if department:
        requests = requests.filter(
            department_id=department
        )

    departments = Department.objects.filter(
        is_active=True
    )
    
    staff_members = User.objects.filter(
    role=User.Roles.STAFF,
    is_active=True
)
    return render(
        request,
        "admin_panel/requests.html",
        {
            "requests": requests,
            "search": search,
            "selected_status": status,
            "selected_department": department,
            "status_choices": Request.Status.choices,
            "departments": departments,
            "staff_members": staff_members,
        }
    )

@admin_required
def admin_assign_request(request, ticket_number):

    help_request = get_object_or_404(
        Request,
        ticket_number=ticket_number
    )

    if request.method == "POST":

        staff_id = request.POST.get(
            "assigned_staff"
        )

        if staff_id:

            staff_member = get_object_or_404(
                User,
                id=staff_id,
                role=User.Roles.STAFF
            )

            help_request.assigned_staff = staff_member

            if help_request.status == Request.Status.PENDING:
                help_request.status = Request.Status.ASSIGNED

            help_request.save()

            Notification.objects.create(
                user=staff_member,
                title="New Request Assigned",
                message=(
                    f"Request {help_request.ticket_number} "
                    f"has been assigned to you."
                ),
                notification_type=Notification.NotificationType.REQUEST,
                request=help_request,
            )

            Notification.objects.create(
                user=help_request.student,
                title="Request Assigned",
                message=(
                    f"Your request {help_request.ticket_number} "
                    f"has been assigned to staff."
                ),
                notification_type=Notification.NotificationType.REQUEST,
                request=help_request,
            )

            messages.success(
                request,
                "Request assigned successfully."
            )

    return redirect(
        "helpdesk:admin_requests"
    )

@admin_required
def admin_departments(request):

    departments = Department.objects.all().order_by("name")

    return render(
        request,
        "admin_panel/departments.html",
        {
            "departments": departments
        }
    )
@login_required
@admin_required
def admin_add_staff(request):
    departments = Department.objects.filter(is_active=True)

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "")
        department_id = request.POST.get("department", "").strip()
        designation = request.POST.get("designation", "").strip()

        errors = []

        if not username or not email or not password:
            errors.append("Username, email and password are required.")

        if User.objects.filter(username__iexact=username).exists():
            errors.append("Username already exists.")

        if User.objects.filter(email__iexact=email).exists():
            errors.append("Email already exists.")

        department = None

        if department_id:
            if department_id.isdigit():
                department = Department.objects.filter(
                    pk=int(department_id),
                    is_active=True,
                ).first()

            if department is None:
                errors.append("Select a valid active department.")

        if password:
            try:
                validate_password(password)
            except ValidationError as exc:
                errors.extend(exc.messages)

        if errors:
            for error in errors:
                messages.error(request, error)

            return render(
                request,
                "admin_panel/add_staff.html",
                {"departments": departments},
            )

        staff = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            role=User.Roles.STAFF,
        )
        staff.set_password(password)
        staff.save()

        StaffProfile.objects.create(
            user=staff,
            department=department,
            designation=designation,
        )

        messages.success(
            request,
            f"Staff account '{staff.username}' created successfully.",
        )

        return redirect("helpdesk:admin_staff")

    return render(
        request,
        "admin_panel/add_staff.html",
        {"departments": departments},
    )

# ==============================
# ADMIN: DEPARTMENT MANAGEMENT
# ==============================

@admin_required
def admin_add_department(request):
    form = DepartmentForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Department added successfully.")
        return redirect("helpdesk:admin_departments")

    return render(request, "admin_panel/department_form.html", {
        "form": form,
        "page_title": "Add Department",
    })


@admin_required
def admin_edit_department(request, department_id):
    department = get_object_or_404(Department, pk=department_id)
    form = DepartmentForm(request.POST or None, instance=department)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Department updated successfully.")
        return redirect("helpdesk:admin_departments")

    return render(request, "admin_panel/department_form.html", {
        "form": form,
        "page_title": "Edit Department",
        "department": department,
    })


# ==============================
# ADMIN: CATEGORY MANAGEMENT
# ==============================

@admin_required
def admin_categories(request):
    categories = Category.objects.select_related(
        "department"
    ).order_by("department__name", "name")

    return render(request, "admin_panel/categories.html", {
        "categories": categories,
    })


@admin_required
def admin_add_category(request):
    form = CategoryForm(request.POST or None)

    # Only show active departments for new categories.
    form.fields["department"].queryset = Department.objects.filter(
        is_active=True
    ).order_by("name")

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Category added successfully.")
        return redirect("helpdesk:admin_categories")

    return render(request, "admin_panel/category_form.html", {
        "form": form,
        "page_title": "Add Category",
    })


@admin_required
def admin_edit_category(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    form = CategoryForm(request.POST or None, instance=category)

    # Include the category's current department even if inactive.
    form.fields["department"].queryset = Department.objects.filter(
        models.Q(is_active=True) | models.Q(pk=category.department_id)
    ).order_by("name")

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Category updated successfully.")
        return redirect("helpdesk:admin_categories")

    return render(request, "admin_panel/category_form.html", {
        "form": form,
        "page_title": "Edit Category",
        "category": category,
    })


@admin_required
def admin_staff_detail(request, staff_id):
    staff = get_object_or_404(
        User.objects.select_related("staff_profile__department"),
        pk=staff_id,
        role=User.Roles.STAFF,
    )

    profile = getattr(staff, "staff_profile", None)

    return render(
        request,
        "admin_panel/staff_detail.html",
        {
            "staff_member": staff,
            "profile": profile,
        },
    )


@admin_required
def admin_edit_staff(request, staff_id):
    staff = get_object_or_404(
        User,
        pk=staff_id,
        role=User.Roles.STAFF,
    )

    profile, _ = StaffProfile.objects.get_or_create(user=staff)
    departments = Department.objects.filter(is_active=True)

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        phone = request.POST.get("phone", "").strip()
        designation = request.POST.get("designation", "").strip()
        department_id = request.POST.get("department", "").strip()

        if not username or not email:
            messages.error(request, "Username and email are required.")
        elif User.objects.filter(
            username__iexact=username
        ).exclude(pk=staff.pk).exists():
            messages.error(request, "That username is already in use.")
        elif User.objects.filter(
            email__iexact=email
        ).exclude(pk=staff.pk).exists():
            messages.error(request, "That email is already in use.")
        else:
            department = None

            if department_id:
                department = Department.objects.filter(
                    pk=department_id,
                    is_active=True,
                ).first()

                if department is None:
                    messages.error(request, "Select a valid department.")
                    return render(
                        request,
                        "admin_panel/staff_edit.html",
                        {
                            "staff": staff,
                            "profile": profile,
                            "departments": departments,
                        },
                    )

            staff.username = username
            staff.first_name = first_name
            staff.last_name = last_name
            staff.email = email
            staff.phone = phone
            staff.save()

            profile.department = department
            profile.designation = designation
            profile.save()

            messages.success(request, "Staff details updated successfully.")
            return redirect(
                "helpdesk:admin_staff_detail",
                staff_id=staff.pk,
            )

    return render(
        request,
        "admin_panel/staff_edit.html",
        {
            "staff": staff,
            "staff_member": staff,
            "profile": profile,
            "departments": departments,
        },
    )


@require_POST
@admin_required
def admin_delete_staff(request, staff_id):
    staff = get_object_or_404(
        User,
        pk=staff_id,
        role=User.Roles.STAFF,
    )

    if staff.pk == request.user.pk:
        messages.error(request, "You cannot delete your own account here.")
        return redirect("helpdesk:admin_staff")

    username = staff.username
    staff.delete()

    messages.success(request, f"Staff account '{username}' was deleted.")
    return redirect("helpdesk:admin_staff")



@admin_required
def admin_reset_staff_password(request, staff_id):
    staff = get_object_or_404(
        User,
        pk=staff_id,
        role=User.Roles.STAFF,
    )

    if request.method == "POST":
        # IMPORTANT: Match the input names in the HTML form.
        password = request.POST.get("new_password", "")
        confirmation = request.POST.get("confirm_password", "")

        if not password or not confirmation:
            messages.error(
                request,
                "Please enter and confirm the new password.",
            )

        elif password != confirmation:
            messages.error(
                request,
                "The passwords do not match.",
            )

        else:
            try:
                validate_password(password, user=staff)

            except ValidationError as exc:
                for error in exc.messages:
                    messages.error(request, error)

            else:
                staff.set_password(password)
                staff.save(update_fields=["password"])

                messages.success(
                    request,
                    f"Password reset successfully for {staff.username}.",
                )

                return redirect(
                    "helpdesk:admin_staff_detail",
                    staff_id=staff.pk,
                )

    return render(
        request,
        "admin_panel/staff_reset_password.html",
        {
            "staff": staff,
            "staff_member": staff,
        },
    )


def department_directory(request):
    departments = Department.objects.filter(
        is_active=True
    ).order_by("name")

    # Each department gets a visual card image.
    # These are remote images; replace with local static files
    # later if you prefer to host them yourself.
    department_images = [
        "https://images.unsplash.com/photo-1562774053-701939374585?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1532094349884-543bc11b234d?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1498243691581-b145c3f54a5a?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=900&q=80",
    ]

    department_cards = [
        {
            "department": department,
            "image": department_images[index % len(department_images)],
        }
        for index, department in enumerate(departments)
    ]

    return render(
        request,
        "helpdesk/department_directory.html",
        {
            "departments": departments,
            "department_cards": department_cards,
        },
    )


def department_detail(request, department_id):
    department = get_object_or_404(
        Department,
        pk=department_id,
        is_active=True,
    )

    staff_profiles = (
        StaffProfile.objects
        .filter(department=department)
        .select_related("user", "department")
        .order_by("designation", "user__first_name", "user__last_name")
    )

    return render(
        request,
        "helpdesk/department_detail.html",
        {
            "department": department,
            "staff_profiles": staff_profiles,
        },
    )

