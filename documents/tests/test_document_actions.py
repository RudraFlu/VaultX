
import tempfile
import shutil
import os

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.urls import reverse

from documents.models import Document

User = get_user_model()


class DocumentActionsTests(TestCase):

    def setUp(self):
        self.media_dir = tempfile.mkdtemp()
        self.settings_override = override_settings(
            MEDIA_ROOT=self.media_dir
        )
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.addCleanup(shutil.rmtree, self.media_dir, True)

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

        self.doc = Document.objects.create(
            owner=self.user1,
            title="Test Document",
            file=ContentFile(b"Sample document content", name="test.txt")
        )

    def test_user_can_download_own_document(self):
        self.client.force_login(self.user1)

        response = self.client.get(
            reverse("download_document", args=[self.doc.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            b"".join(response.streaming_content),
            b"Sample document content"
        )

    def test_download_increments_download_count(self):
        self.client.force_login(self.user1)

        self.client.get(
            reverse("download_document", args=[self.doc.pk])
        )

        self.doc.refresh_from_db()
        self.assertEqual(self.doc.downloads, 1)

    def test_user_cannot_download_another_users_document(self):
        self.client.force_login(self.user2)

        response = self.client.get(
            reverse("download_document", args=[self.doc.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_user_can_delete_own_document(self):
        self.client.force_login(self.user1)

        response = self.client.post(
            reverse("delete_document", args=[self.doc.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Document.objects.filter(pk=self.doc.pk).exists()
        )

    def test_user_cannot_delete_another_users_document(self):
        self.client.force_login(self.user2)

        response = self.client.post(
            reverse("delete_document", args=[self.doc.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            Document.objects.filter(pk=self.doc.pk).exists()
        )

    def test_delete_requires_post_method(self):
        self.client.force_login(self.user1)

        response = self.client.get(
            reverse("delete_document", args=[self.doc.pk])
        )

        self.assertEqual(response.status_code, 405)
