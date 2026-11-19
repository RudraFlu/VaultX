from django.db import connection
import re

def create_search_index():
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS document_search
            USING fts5(
                file_path UNINDEXED,
                filename,
                content,
                tokenize='unicode61'
            )
        """)

    print("Document search index is ready!")


def add_to_index(file_path, filename, content):
    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM document_search WHERE file_path = %s",
            [file_path],
        )

        cursor.execute("""
            INSERT INTO document_search
            (file_path, filename, content)
            VALUES (%s, %s, %s)
        """, [file_path, filename, content])


def remove_from_index(file_path):
    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM document_search WHERE file_path = %s",
            [file_path],
        )


def get_index_count():
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM document_search")
        return cursor.fetchone()[0]

def search_documents(query, limit=100):
    terms = re.findall(r"\w+", query.casefold())

    if not terms:
        return []

    fts_query = " OR ".join(
        f'"{term}"' for term in terms
    )

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                file_path,
                filename,
                snippet(document_search, 2, '<b>', '</b>', '...', 20)
                    AS excerpt,
                bm25(document_search, 0.0, 5.0, 1.0)
                    AS relevance
            FROM document_search
            WHERE document_search MATCH %s
            ORDER BY relevance
            LIMIT %s
        """, [fts_query, limit])

        rows = cursor.fetchall()

    return [
        {
            "path": row[0],
            "filename": row[1],
            "excerpt": row[2],
            "relevance": row[3],
        }
        for row in rows
    ]
