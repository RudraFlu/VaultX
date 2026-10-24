
from django import forms
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages


COLLEGE_EMAIL_DOMAIN = "@mail.jiit.ac.in"


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=6,
        label="Password",
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirm password",
    )

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()

        if not email.endswith(COLLEGE_EMAIL_DOMAIN):
            raise forms.ValidationError(
                "Please use your college email address."
            )

        return email

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match.")

        return cleaned_data


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.is_active = False
            user.save()

            messages.success(
                request,
                "Account created. Email verification will be available next."
            )
            return redirect("register")
    else:
        form = RegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    return render(request, "accounts/login.html")


def logout_view(request):
    pass
