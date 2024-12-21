from django.test import TestCase, Client
from django.urls import reverse
from datetime import datetime, timedelta
from User_app.forms import EventForm

class EventFormTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.valid_event_data = {
            'EventType': 'Conference',
            'EventTitle': 'Tech Summit 2024',
            'EventDescription': 'Annual Technology Conference',
            'EventDate': (datetime.now().date() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'EventTime': '14:00',
            'EventCost': '500 SAR',
            'EventCapacity': 200,
            'EventLocation': 'https://maps.google.com/test-venue'
        }

    def test_valid_event_creation(self):
        """Test creating event with valid data"""
        form = EventForm(data=self.valid_event_data)
        self.assertTrue(form.is_valid())

    def test_past_date_validation(self):
        """Test validation of past event dates"""
        past_data = self.valid_event_data.copy()
        past_data['EventDate'] = (datetime.now().date() - timedelta(days=1)).strftime('%Y-%m-%d')
        form = EventForm(data=past_data)
        self.assertFalse(form.is_valid())
        self.assertIn('EventDate', form.errors)

    def test_negative_capacity(self):
        """Test validation of negative event capacity"""
        invalid_capacity = self.valid_event_data.copy()
        invalid_capacity['EventCapacity'] = -50
        form = EventForm(data=invalid_capacity)
        self.assertFalse(form.is_valid())
        self.assertIn('EventCapacity', form.errors)

    def test_invalid_cost_format(self):
        """Test validation of invalid cost formats"""
        invalid_cost = self.valid_event_data.copy()
        invalid_cost['EventCost'] = 'invalid_cost'
        form = EventForm(data=invalid_cost)
        self.assertFalse(form.is_valid())
        self.assertIn('EventCost', form.errors)