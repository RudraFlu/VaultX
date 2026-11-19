
import os
import hashlib
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import connection, transaction

from documents.services import SHARED_ROOT
from documents.search_engine import extract_document_text
from documents.search_index import create_search_index
INDEX_ROOT = SHARED_ROOT / "Computer Science & IT" / "ODD 2026"
SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".doc",
    ".pptx", ".xlsx", ".txt", ".csv",
}


class BaseCommand(BaseCommand):
    pass


class Command(BaseCommand):
    help = "Scan the shared drive and update the document search index."
    def add_arguments(self, parser):
        parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of files to process.",
    )
    def handle(self, *args, **options):
        limit = options.get("limit")
        processed = 0
        self.stdout.write("Starting document indexing...")

        root = SHARED_ROOT

        if not root.exists():
            self.stderr.write(
                self.style.ERROR("Shared drive is unavailable.")
            )
            return

        create_search_index()

        indexed = 0
        skipped = 0
        failed = 0
        scan_errors = []
        seen_paths = set()

        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_index_status (
                    file_path TEXT PRIMARY KEY,
                    file_size INTEGER,
                    modified REAL,
                    file_hash TEXT
                )
            """)
        def handle_scan_error(error):
            scan_errors.append(str(error))
            self.stderr.write(f"Directory scan error: {error}")
        for directory, _, filenames in os.walk(INDEX_ROOT):
            if limit is not None and processed >= limit:
                break
            for filename in filenames:
                if limit is not None and processed >= limit:
                    break
                path = Path(directory) / filename
                if filename.startswith("~$"):
                       continue

                if filename.lower() == "thumbs.db":
                       continue

                if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                    continue

                try:
                    stat = path.stat()
                    relative_path = str(path.relative_to(SHARED_ROOT))
                    seen_paths.add(relative_path)
                    processed += 1
                    file_hash = self.calculate_hash(path)

                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT file_hash
                            FROM document_index_status
                            WHERE file_path = %s
                        """, [relative_path])

                        existing = cursor.fetchone()

                    if existing and existing[0] == file_hash:
                        skipped += 1
                        continue

                    content = extract_document_text(path)

                    with connection.cursor() as cursor:
                        cursor.execute("""
                            DELETE FROM document_search
                            WHERE file_path = %s
                        """, [relative_path])

                        cursor.execute("""
                            INSERT INTO document_search
                            (file_path, filename, content)
                            VALUES (%s, %s, %s)
                        """, [relative_path, filename, content])

                        cursor.execute("""
                            INSERT OR REPLACE INTO document_index_status
                            (file_path, file_size, modified, file_hash)
                            VALUES (%s, %s, %s, %s)
                        """, [
                            relative_path,
                            stat.st_size,
                            stat.st_mtime,
                            file_hash,
                        ])

                    indexed += 1

                except Exception as error:
                    failed += 1
                    self.stderr.write(
                        f"Failed: {path} - {error}"
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Indexing complete. Indexed: {indexed}, "
                f"Unchanged: {skipped}, Failed: {failed}"
            )
        )
        if limit is None and not scan_errors:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT file_path FROM document_index_status"
                    )
                    indexed_paths = {
                        row[0] for row in cursor.fetchall()
                    }

                    stale_paths = indexed_paths - seen_paths

                    for stale_path in stale_paths:
                        cursor.execute(
                    "DELETE FROM document_search WHERE file_path = %s",
                    [stale_path],
                )

                        cursor.execute(
                    "DELETE FROM document_index_status WHERE file_path = %s",
                    [stale_path],
                )

            self.stdout.write(
        f"Removed {len(stale_paths)} deleted files from the index."
    )
        else:
            self.stderr.write(
        "Some directories could not be scanned. "
        "Keeping existing index entries to avoid accidental deletion."
    )
    @staticmethod
    def calculate_hash(path):
        digest = hashlib.sha256()

        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)

        return digest.hexdigest()
