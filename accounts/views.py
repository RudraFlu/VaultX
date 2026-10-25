import re

from django import forms
from django.contrib import messages
from django.contrib.auth.models import User
from django.core import signing
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required

COLLEGE_EMAIL_DOMAIN = "@mail.jiit.ac.in"
VERIFICATION_SALT = "vaultx.email.verification"
VERIFICATION_MAX_AGE = 60 * 60 * 24


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8,
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

        if not re.fullmatch(r"\d+@mail\.jiit\.ac\.in", email):
            raise forms.ValidationError(
                "Use your college email in the format "
                "rollno@mail.jiit.ac.in."
            )

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error(
                "confirm_password",
                "Passwords do not match.",
            )

        return cleaned_data


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data["email"]
            user.set_password(form.cleaned_data["password"])
            user.is_active = False
            user.save()

            token = signing.dumps(
                user.pk,
                salt=VERIFICATION_SALT,
            )

            verification_url = request.build_absolute_uri(
            reverse("verify_email", kwargs={"token": token})
            
)

            try:
                send_mail(
                    subject="Verify your VaultX account",
                    message=(
                        f"Hello {user.username},\n\n"
                        "Click the link below to verify your email "
                        "and activate your VaultX account:\n\n"
                        f"{verification_url}  \n\n"
                        "This link expires in 24 hours."
                    ),
                    from_email=None,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception:
                user.delete()
                messages.error(
                    request,
                    "We couldn't send the verification email. "
                    "Please try again later.",
                )
                return redirect("register")

            messages.success(
                request,
                "Registration successful! Check your email "
                "for the verification link.",
            )
            return redirect("register")

    else:
        form = RegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form},
    )


def verify_email(request, token):
    try:
        user_id = signing.loads(
            token,
            salt=VERIFICATION_SALT,
            max_age=VERIFICATION_MAX_AGE,
        )

        user = User.objects.get(pk=user_id)

    except (
        signing.BadSignature,
        signing.SignatureExpired,
        User.DoesNotExist,
        ValueError,
        TypeError,
    ):
        messages.error(
            request,
            "This verification link is invalid or has expired.",
        )
        return redirect("login")

    if user.is_active:
        messages.info(request, "Your account is already verified.")
    else:
        user.is_active = True
        user.save(update_fields=["is_active"])
        messages.success(
            request,
            "Email verified successfully! You can now log in.",
        )

    return redirect("login")

def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        user = User.objects.filter(email__iexact=email).first()

        if user:
            authenticated_user = authenticate(
                request,
                username=user.username,
                password=password,
            )
        else:
            authenticated_user = None

        if authenticated_user is not None:
            login(request, authenticated_user)
            return redirect("home")

        messages.error(
            request,
            "Invalid email or password, or your account "
            "has not been verified.",
        )

    return render(request, "accounts/login.html")


def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "You have logged out successfully.")

    return redirect("login")