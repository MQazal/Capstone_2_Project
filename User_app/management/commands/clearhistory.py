from django.core.management.base import BaseCommand
from django.contrib.admin.models import LogEntry

class Command(BaseCommand):
    help = 'Clears all admin log entries'

    def handle(self, *args, **kwargs):
        LogEntry.objects.all().delete()
        self.stdout.write('Successfully cleared admin history')