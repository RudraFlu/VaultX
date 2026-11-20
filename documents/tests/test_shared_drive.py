
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase

from documents import services


class SharedDrivePathTests(SimpleTestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        (self.root / "Computer Science").mkdir()
        (self.root / "Computer Science" / "notes.pdf").touch()

        self.root_patch = patch.object(
            services, "SHARED_ROOT", self.root
        )
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.addCleanup(self.temp_dir.cleanup)

    def test_valid_file_path(self):
        result = services.resolve_shared_path(
            "Computer Science/notes.pdf"
        )

        self.assertEqual(
    result,
    (self.root / "Computer Science" / "notes.pdf").resolve()
)
    def test_valid_directory_path(self):
        result = services.resolve_shared_path("Computer Science")

        self.assertEqual(
            result,
            (self.root / "Computer Science").resolve()
        )

    def test_empty_path_returns_root(self):
        result = services.resolve_shared_path("")

        self.assertEqual(result, self.root.resolve())

    def test_rejects_parent_directory_traversal(self):
        result = services.resolve_shared_path("../outside.txt")

        self.assertIsNone(result)

    def test_rejects_windows_traversal(self):
        result = services.resolve_shared_path(
            r"Computer Science\..\..\outside.txt"
        )

        self.assertIsNone(result)

    def test_rejects_absolute_windows_path(self):
        result = services.resolve_shared_path(
            r"C:\Windows\system.ini"
        )

        self.assertIsNone(result)

    def test_rejects_unc_absolute_path(self):
        result = services.resolve_shared_path(
            r"\\another-server\private\file.txt"
        )

        self.assertIsNone(result)

    def test_rejects_non_string_path(self):
        result = services.resolve_shared_path(None)

        self.assertIsNone(result)
