
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from documents.models import Document

User = get_user_model()


class PrivateVaultTests(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@mail.jiit.ac.in",
            password="TestPassword123"
        )

        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@mail.jiit.ac.in",
            password="TestPassword123"
        )

        self.url = reverse("my_vault")

        self.doc1 = Document.objects.create(
            owner=self.user1,
            title="User 1 Document",
            file="documents/user1.pdf"
        )

        self.doc2 = Document.objects.create(
            owner=self.user2,
            title="User 2 Document",
            file="documents/user2.pdf"
        )

    def test_logged_in_user_can_access_vault(self):
        self.client.force_login(self.user1)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_user_sees_only_own_documents(self):
        self.client.force_login(self.user1)

        response = self.client.get(self.url)
        documents = response.context["documents"]

        self.assertIn(self.doc1, documents)
        self.assertNotIn(self.doc2, documents)

    def test_user_cannot_access_another_users_documents(self):
        self.client.force_login(self.user2)

        response = self.client.get(self.url)
        documents = response.context["documents"]

        self.assertIn(self.doc2, documents)
        self.assertNotIn(self.doc1, documents)

    def test_unauthenticated_user_is_redirected(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response.url.startswith(reverse("login"))
        )
