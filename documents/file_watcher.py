
import logging
import time
from pathlib import Path
from documents.indexing_queue import enqueue_file
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from threading import Thread
from documents.indexing_worker import start_worker
from documents.services import SHARED_ROOT
WATCH_ROOT = SHARED_ROOT / "Computer Science & IT" / "ODD 2026"
logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".doc",
    ".pptx", ".xlsx", ".txt", ".csv",
}


class SharedDriveHandler(FileSystemEventHandler):

    def on_created(self, event):
        if not event.is_directory:
            self.process_event("created", event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.process_event("modified", event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self.process_event("deleted", event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.process_event("deleted", event.src_path)
            self.process_event("created", event.dest_path)

    def process_event(self, action, file_path):
        path = Path(file_path)

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return

        try:
            relative_path = str(path.relative_to(SHARED_ROOT))

            logger.info(
                "Filesystem event: %s | %s",
                action,
                relative_path,
            )
            enqueue_file(action, relative_path)

            print(f"[QUEUED] {action.upper()} {relative_path}")
        except ValueError:
            logger.warning("Path outside shared root: %s", file_path)


def start_watcher():
    if not WATCH_ROOT.is_dir():
        raise RuntimeError("ODD 2026 shared folder is unavailable.")
    observer = Observer()

    handler = SharedDriveHandler()

    observer.schedule(
        handler,
        str(WATCH_ROOT),
        recursive=True,
    )

    observer.start()
    worker_thread = Thread(
    target=start_worker,
    daemon=True
)
    worker_thread.start()
    logger.info("Watching shared drive: %s", SHARED_ROOT)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping filesystem watcher...")
        observer.stop()

    observer.join()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_watcher()
