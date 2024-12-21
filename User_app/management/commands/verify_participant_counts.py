# management/commands/verify_participant_counts.py
from django.core.management.base import BaseCommand
from User_app.models import Event, EventRegistration

class Command(BaseCommand):
    help = 'Verify and fix participant counts for events'

    def handle(self, *args, **options):
        for event in Event.objects.all():
            actual_count = EventRegistration.objects.filter(
                event=event, 
                status='REGISTERED'
            ).count()
            if event.current_participants != actual_count:
                event.current_participants = actual_count
                event.save()
                self.stdout.write(
                    f"Fixed count for {event.EventTitle}: {actual_count}"
                )