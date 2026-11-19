import logging
import time
from pathlib import Path

from documents.indexing_queue import get_next_event, finish_event
from documents.services import SHARED_ROOT
from documents.search_engine import extract_document_text
from documents.search_index import add_to_index, remove_from_index

logger = logging.getLogger(__name__)


def process_event(action, relative_path):
    file_path = (SHARED_ROOT / relative_path).resolve()

    try:
        file_path.relative_to(SHARED_ROOT.resolve())

        if action == "deleted":
            remove_from_index(relative_path)
            logger.info("Removed from index: %s", relative_path)
            return

        content = None

        for attempt in range(5):
            try:
                if file_path.is_file():
                    content = extract_document_text(file_path)
                    break

            except (PermissionError, OSError):
                logger.warning(
                    "File not ready, retrying (%s/5): %s",
                    attempt + 1,
                    relative_path
                )

            time.sleep(3)

        if content is None:
            logger.error("Could not read file: %s", relative_path)
            return

        add_to_index(
            relative_path,
            file_path.name,
            content
        )

        logger.info("Indexed: %s", relative_path)

    except Exception:
        logger.exception("Failed to process %s", relative_path)

def start_worker():
    logger.info("Indexing worker started.")

    while True:
        action, relative_path = get_next_event()

        try:
            process_event(action, relative_path)
        finally:
            finish_event(relative_path)
