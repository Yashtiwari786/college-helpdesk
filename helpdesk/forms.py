from django import forms
from django.core.exceptions import ValidationError
from .models import Request, Message, Feedback


class RequestForm(forms.ModelForm):

    class Meta:

        model = Request

        fields = [
            "department",
            "category",
            "subject",
            "description",
            "priority",
        ]

        widgets = {

            "department": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "category": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "subject": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: Wi-Fi not working",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": (
                        "Describe your problem clearly..."
                    ),
                }
            ),

            "priority": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }

    def clean(self):

        cleaned_data = super().clean()

        department = cleaned_data.get("department")
        category = cleaned_data.get("category")

        if (
            department
            and category
            and category.department_id != department.id
        ):
            raise forms.ValidationError(
                "Selected category does not belong "
                "to the selected department."
            )

        return cleaned_data


class MessageForm(forms.ModelForm):

    class Meta:

        model = Message

        fields = [
            "message",
            "attachment",
        ]

        widgets = {

            "message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": (
                        "Write your message..."
                    ),
                }
            ),

            "attachment": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                }
            ),
        }


class FeedbackForm(forms.ModelForm):

    class Meta:

        model = Feedback

        fields = [
            "rating",
            "comment",
        ]

        widgets = {

            "rating": forms.Select(
                choices=[
                    (5, "★★★★★ Excellent"),
                    (4, "★★★★ Very Good"),
                    (3, "★★★ Good"),
                    (2, "★★ Poor"),
                    (1, "★ Very Poor"),
                ],
                attrs={
                    "class": "form-select",
                }
            ),

            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Tell us about your experience..."
                    ),
                }
            ),
        }

def validate_file_size(file):

    max_size = 10 * 1024 * 1024

    if file.size > max_size:

        raise ValidationError(
            "File size cannot exceed 10 MB."
        )

from django import forms
from .models import Request, Message


class StaffRequestUpdateForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = ["status", "priority", "assigned_staff"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "assigned_staff": forms.Select(attrs={"class": "form-select"}),
        }


class StaffMessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["message", "attachment"]
        widgets = {
            "message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Write a reply to the student..."
                }
            ),
            "attachment": forms.ClearableFileInput(
                attrs={"class": "form-control"}
            ),
        }