
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from documents.models import Document
import tempfile

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
class DocumentUploadTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@mail.jiit.ac.in",
            password="TestPassword123"
        )
        self.client.force_login(self.user)

        self.url = reverse("upload_doc")

    def create_file(self, name="test.pdf", content=b"Test PDF content"):
        return SimpleUploadedFile(
            name,
            content,
            content_type="application/pdf"
        )

    def test_upload_page_loads(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_valid_pdf_upload(self):
        response = self.client.post(self.url, {
            "title": "Test Document",
            "description": "Test description",
            "file": self.create_file(),
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Document.objects.filter(
                owner=self.user,
                title="Test Document"
            ).exists()
        )

    def test_upload_rejects_invalid_extension(self):
        response = self.client.post(self.url, {
            "title": "Invalid File",
            "description": "",
            "file": self.create_file("test.exe"),
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Document.objects.count(), 0)

    def test_upload_rejects_file_over_100mb(self):
        large_file = SimpleUploadedFile(
            "large.pdf",
            b"x" * (100 * 1024 * 1024 + 1),
            content_type="application/pdf"
        )

        response = self.client.post(self.url, {
            "title": "Large File",
            "description": "",
            "file": large_file,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Document.objects.count(), 0)

    def test_uploaded_document_is_private(self):
        self.client.post(self.url, {
            "title": "Private Document",
            "description": "",
            "file": self.create_file(),
        })

        document = Document.objects.get(title="Private Document")
        self.assertEqual(document.visibility, "PRIVATE")
        self.assertEqual(document.owner, self.user)
