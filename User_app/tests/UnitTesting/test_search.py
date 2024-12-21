from django.test import TestCase, Client
from django.urls import reverse
from datetime import datetime, timedelta
from User_app.models import Event

class EventSearchAndFilterTests(TestCase):
    def setUp(self):
        # Create various test events
        Event.objects.create(
            EventType="Conference",
            EventTitle="Tech Conference 2024",
            EventDate=datetime.now().date() + timedelta(days=30),
            EventTime=datetime.now().time(),
            EventCost="1000 SAR"
        )
        Event.objects.create(
            EventType="Workshop",
            EventTitle="Python Workshop",
            EventDate=datetime.now().date() + timedelta(days=15),
            EventTime=datetime.now().time(),
            EventCost="Free"
        )
        Event.objects.create(
            EventType="Conference",
            EventTitle="Data Science Summit",
            EventDate=datetime.now().date() + timedelta(days=45),
            EventTime=datetime.now().time(),
            EventCost="750 SAR"
        )

    def test_event_type_filter(self):
        """Test filtering events by type"""
        response = self.client.get(reverse('search_events'), {'event_type': 'Conference'})
        self.assertEqual(len(response.context['events']), 2)

    def test_free_events_filter(self):
        """Test filtering for free events"""
        free_events = Event.objects.filter(EventCost="Free")
        self.assertEqual(free_events.count(), 1)
        self.assertEqual(free_events.first().EventTitle, "Python Workshop")