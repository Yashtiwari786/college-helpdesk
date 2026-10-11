from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Roles(models.TextChoices):
        STUDENT = "STUDENT", "Student"
        STAFF = "STAFF", "Staff"
        ADMIN = "ADMIN", "Admin"

    email = models.EmailField(
        unique=True
    )

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.STUDENT,
        db_index=True,
    )

    
    department = models.ForeignKey(
        "helpdesk.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
    )


    phone = models.CharField(
        max_length=20,
        blank=True,
    )

    profile_photo = models.URLField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_student(self):
        return self.role == self.Roles.STUDENT

    @property
    def is_staff_member(self):
        return self.role == self.Roles.STAFF

    @property
    def is_admin_user(self):
        return self.role == self.Roles.ADMIN
