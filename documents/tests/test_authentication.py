from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.core import mail
import re


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AuthenticationTests(TestCase):

    def setUp(self):
        self.register_url = reverse("register")
        self.login_url = reverse("login")

        self.valid_data = {
            "username": "student123",
            "email": "123456@mail.jiit.ac.in",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
        }

    # Test 1: Registration page loads
    def test_registration_page_loads(self):
        response = self.client.get(self.register_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Register")

    # Test 2: Valid registration creates inactive account
    def test_valid_registration(self):
        response = self.client.post(
            self.register_url,
            self.valid_data
        )

        user = User.objects.get(username="student123")

        self.assertEqual(response.status_code, 302)
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)

    # Test 3: Invalid college email is rejected
    def test_invalid_college_email(self):
        data = self.valid_data.copy()
        data["email"] = "student@gmail.com"

        self.client.post(self.register_url, data)

        self.assertFalse(
            User.objects.filter(username="student123").exists()
        )

    # Test 4: Password mismatch is rejected
    def test_password_mismatch(self):
        data = self.valid_data.copy()
        data["confirm_password"] = "DifferentPass123"

        self.client.post(self.register_url, data)

        self.assertFalse(
            User.objects.filter(username="student123").exists()
        )

    # Test 5: Duplicate email is rejected
    def test_duplicate_email(self):
        User.objects.create_user(
            username="existing",
            email="123456@mail.jiit.ac.in",
            password="ExistingPass123"
        )

        self.client.post(self.register_url, self.valid_data)

        self.assertEqual(User.objects.count(), 1)

    # Test 6: Email verification activates account
    def test_email_verification(self):
        self.client.post(self.register_url, self.valid_data)

        user = User.objects.get(username="student123")

        email_body = mail.outbox[0].body

        match = re.search(r"/verify/([^\s]+)", email_body)
        self.assertIsNotNone(match)

        token = match.group(1)

        match = re.search(
    r"https?://[^\s]+",
    email_body
)

        self.assertIsNotNone(match)

        verification_url = match.group(0).strip()

        response = self.client.get(verification_url)
        user.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertTrue(user.is_active)

    # Test 7: Active user can log in
    def test_valid_login(self):
        User.objects.create_user(
            username="student123",
            email="123456@mail.jiit.ac.in",
            password="StrongPass123",
            is_active=True
        )

        response = self.client.post(
            self.login_url,
            {
                "email": "123456@mail.jiit.ac.in",
                "password": "StrongPass123",
            }
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    # Test 8: Inactive user cannot log in
    def test_unverified_user_login(self):
        User.objects.create_user(
            username="student123",
            email="123456@mail.jiit.ac.in",
            password="StrongPass123",
            is_active=False
        )

        response = self.client.post(
            self.login_url,
            {
                "email": "123456@mail.jiit.ac.in",
                "password": "StrongPass123",
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    # Test 9: Incorrect password is rejected
    def test_invalid_password(self):
        User.objects.create_user(
            username="student123",
            email="123456@mail.jiit.ac.in",
            password="StrongPass123",
            is_active=True
        )

        response = self.client.post(
            self.login_url,
            {
                "email": "123456@mail.jiit.ac.in",
                "password": "WrongPassword123",
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    # Test 10: Duplicate username is rejected
    def test_duplicate_username(self):
        User.objects.create_user(
            username="student123",
            email="654321@mail.jiit.ac.in",
            password="ExistingPass123"
        )

        self.client.post(self.register_url, self.valid_data)

        self.assertEqual(User.objects.count(), 1)
