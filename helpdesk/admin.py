from django.contrib import admin
from .models import FAQ, Announcement
from .models import (
    Department,
    Category,
    Request,
    Attachment,
    Message,
    Notification,
    Feedback,
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "department",
        "is_active",
    )

    list_filter = (
        "department",
        "is_active",
    )

    search_fields = (
        "name",
    )


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):

    list_display = (
        "ticket_number",
        "subject",
        "student",
        "department",
        "assigned_staff",
        "priority",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "priority",
        "department",
    )

    search_fields = (
        "ticket_number",
        "subject",
        "description",
        "student__username",
        "student__email",
    )

    readonly_fields = (
        "ticket_number",
        "created_at",
        "updated_at",
        "resolved_at",
        "closed_at",
    )


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):

    list_display = (
        "original_name",
        "request",
        "uploaded_by",
        "uploaded_at",
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):

    list_display = (
        "request",
        "sender",
        "created_at",
        "is_read",
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "user",
        "notification_type",
        "is_read",
        "created_at",
    )

    list_filter = (
        "notification_type",
        "is_read",
    )


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):

    list_display = (
        "request",
        "student",
        "rating",
        "created_at",
    )

    list_filter = (
        "rating",
    )

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = (
        "question",
        "department",
        "is_active",
        "created_at",
    )

    list_filter = (
        "department",
        "is_active",
    )

    search_fields = (
        "question",
        "answer",
    )


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "department",
        "is_active",
        "created_at",
    )

    list_filter = (
        "department",
        "is_active",
    )

    search_fields = (
        "title",
        "message",
    )