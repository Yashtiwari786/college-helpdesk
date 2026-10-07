from django.contrib import messages
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