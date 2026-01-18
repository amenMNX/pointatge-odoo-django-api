# attendance/management/commands/sync_odoo.py
from django.core.management.base import BaseCommand
from attendance.odoo_sync import sync_pointages_to_odoo

class Command(BaseCommand):
    help = "Sync unsynced pointages to Odoo"

    def handle(self, *args, **kwargs):
        try:
            sync_pointages_to_odoo()
            self.stdout.write(self.style.SUCCESS("Pointages synced successfully"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Sync failed: {e}"))
