import logging

from django.core.management.base import BaseCommand
from documents.file_watcher import start_watcher


class Command(BaseCommand):
    help = "Start the VaultX shared-drive file watcher"

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO)

        self.stdout.write(
            self.style.SUCCESS("Starting VaultX file watcher...")
        )

        start_watcher()
