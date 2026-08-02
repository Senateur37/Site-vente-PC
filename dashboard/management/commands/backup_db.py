from django.core.management.base import BaseCommand
from django.conf import settings
import shutil
import os
from datetime import datetime


class Command(BaseCommand):
    help = "Sauvegarde la base de données dans un dossier backups/"

    def handle(self, *args, **options):
        db_path = settings.DATABASES['default']['NAME']
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        horodatage = datetime.now().strftime('%Y%m%d_%H%M%S')
        destination = os.path.join(backup_dir, f"db_{horodatage}.sqlite3")

        shutil.copy2(db_path, destination)
        self.stdout.write(self.style.SUCCESS(f"Sauvegarde créée : {destination}"))
