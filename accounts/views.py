from django.contrib.auth import login
from django.shortcuts import render, redirect

from .forms import StudentRegistrationForm


def register(request):

    if request.user.is_authenticated:
        return redirect("dashboard:dashboard")

    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()

            # Automatically log the newly registered student in
            login(request, user)

            return redirect("dashboard:dashboard")

    else:
        form = StudentRegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )