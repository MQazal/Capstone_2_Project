from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps

class Command(BaseCommand):
    help = 'Reset the auto-increment counter for EventID and initialize event fields'

    def handle(self, *args, **options):
        # Get the models
        Event = apps.get_model('User_app', 'Event')
        EventFormField = apps.get_model('User_app', 'EventFormField')
        
        # Delete all events and their related form fields
        self.stdout.write('Deleting all events and form fields...')
        Event.objects.all().delete()
        
        # Reset the sequence - execute statements one at a time
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='User_app_event'")
            
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='User_app_eventformfield'")
        
        self.stdout.write(self.style.SUCCESS('Successfully reset EventID and EventFormField sequences'))