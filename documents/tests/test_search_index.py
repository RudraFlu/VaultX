
from django.test import TestCase

from documents.search_index import (
    create_search_index,
    add_to_index,
    remove_from_index,
    get_index_count,
    search_documents,
)


class SearchIndexTests(TestCase):

    def setUp(self):
        create_search_index()

        # Keep tests isolated from previously indexed records.
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM document_search")

    def test_create_search_index(self):
        # Calling it twice should not raise an error.
        create_search_index()

    def test_add_document_to_index(self):
        add_to_index(
            "docs/test.pdf",
            "test.pdf",
            "This document contains Python programming notes"
        )

        self.assertEqual(get_index_count(), 1)

    def test_update_existing_document(self):
        add_to_index(
            "docs/test.pdf",
            "test.pdf",
            "Old document content"
        )

        add_to_index(
            "docs/test.pdf",
            "test.pdf",
            "Updated Python content"
        )

        self.assertEqual(get_index_count(), 1)

        results = search_documents("Python")
        self.assertEqual(len(results), 1)

    def test_remove_document_from_index(self):
        add_to_index(
            "docs/test.pdf",
            "test.pdf",
            "Python programming"
        )

        remove_from_index("docs/test.pdf")

        self.assertEqual(get_index_count(), 0)

    def test_search_by_filename(self):
        add_to_index(
            "docs/networking.pdf",
            "networking.pdf",
            "Some unrelated content"
        )

        results = search_documents("networking")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["filename"], "networking.pdf")

    def test_search_by_content(self):
        add_to_index(
            "docs/notes.pdf",
            "notes.pdf",
            "TCP is a reliable transport protocol"
        )

        results = search_documents("reliable")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["path"], "docs/notes.pdf")

    def test_empty_search_query(self):
        self.assertEqual(search_documents(""), [])
        self.assertEqual(search_documents("!!!"), [])

    def test_search_result_limit(self):
        for i in range(3):
            add_to_index(
                f"docs/file{i}.pdf",
                f"file{i}.pdf",
                "Python programming notes"
            )

        results = search_documents("Python", limit=2)

        self.assertEqual(len(results), 2)
