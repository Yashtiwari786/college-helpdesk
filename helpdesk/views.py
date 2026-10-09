from django.contrib import messages
from functools import wraps
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db import models
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
    Announcement
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


@student_required
def create_request(request):

    if request.method == "POST":

        form = RequestForm(
            request.POST
        )

        if form.is_valid():

            help_request = form.save(
                commit=False
            )

            help_request.student = request.user

            help_request.save()


            # Notification for student

            Notification.objects.create(
                user=request.user,
                title="Request Created",
                message=(
                    f"Your request "
                    f"{help_request.ticket_number} "
                    f"has been created successfully."
                ),
                notification_type=(
                    Notification.NotificationType.REQUEST
                ),
                request=help_request,
            )


            # Attachments

            files = request.FILES.getlist(
                "attachments"
            )

            for uploaded_file in files:

                Attachment.objects.create(
                    request=help_request,
                    uploaded_by=request.user,
                    file=uploaded_file,
                )


            messages.success(
                request,
                (
                    f"Request "
                    f"{help_request.ticket_number} "
                    f"created successfully."
                )
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
        {
            "form": form,
        }
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

    staff_members = User.objects.filter(
        role=User.Roles.STAFF
    ).order_by(
        "-date_joined"
    )

    search = request.GET.get("search", "").strip()

    if search:
        staff_members = staff_members.filter(
            Q(username__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(email__icontains=search)
        )

    return render(
        request,
        "admin_panel/staff.html",
        {
            "staff_members": staff_members,
            "search": search,
        }
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
def admin_add_staff(request):

    user = request.user

    if user.role != user.Roles.ADMIN:
        return redirect("dashboard:dashboard")

    if request.method == "POST":

        username = request.POST.get("username", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        if not username or not email or not password:
            messages.error(
                request,
                "Username, email and password are required."
            )
            return render(
                request,
                "admin_panel/add_staff.html"
            )

        if User.objects.filter(username=username).exists():
            messages.error(
                request,
                "Username already exists."
            )
            return render(
                request,
                "admin_panel/add_staff.html"
            )

        if User.objects.filter(email=email).exists():
            messages.error(
                request,
                "Email already exists."
            )
            return render(
                request,
                "admin_panel/add_staff.html"
            )

        staff = User.objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=User.Roles.STAFF,
            password=make_password(password),
        )

        messages.success(
            request,
            f"Staff account '{staff.username}' created successfully."
        )

        return redirect("helpdesk:admin_staff")

    return render(
        request,
        "admin_panel/add_staff.html"
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