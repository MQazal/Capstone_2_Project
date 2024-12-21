from django.test import TestCase
from django.urls import reverse
from datetime import datetime, timedelta
from User_app.models import Event, EventFormField

class EventModelTests(TestCase):
    def setUp(self):
        self.test_event = Event.objects.create(
            EventType="Conference",
            EventTitle="Python Summit 2024",
            EventDescription="Annual Python Conference",
            EventDate=datetime.now().date() + timedelta(days=30),
            EventTime=datetime.now().time(),
            EventCost="500 SAR",
            EventLocation="https://maps.google.com/test-location",
            EventCapacity=100
        )

    def test_event_str_representation(self):
        self.assertEqual(str(self.test_event), "Python Summit 2024")

    def test_event_capacity_management(self):
        self.assertEqual(self.test_event.current_participants, 0)
        self.assertFalse(self.test_event.is_full())

        for _ in range(50):
            self.assertTrue(self.test_event.add_participant())
        self.assertEqual(self.test_event.current_participants, 50)

        self.assertTrue(self.test_event.remove_participant())
        self.assertEqual(self.test_event.current_participants, 49)

        self.test_event.current_participants = 100
        self.test_event.save()
        self.assertTrue(self.test_event.is_full())
        self.assertFalse(self.test_event.add_participant())

class EventFormFieldTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            EventType="Workshop",
            EventTitle="Django Testing Workshop",
            EventDate=datetime.now().date() + timedelta(days=15),
            EventTime=datetime.now().time(),
            EventCost="Free"
        )

    def test_form_field_creation(self):
        text_field = EventFormField.objects.create(
            event=self.event,
            field_name="Full Name",
            field_type="text",
            is_required=True
        )
        self.assertEqual(str(text_field), "Django Testing Workshop - Full Name")

        select_field = EventFormField.objects.create(
            event=self.event,
            field_name="T-Shirt Size",
            field_type="select",
            is_required=True,
            choices="S,M,L,XL"
        )
        self.assertTrue(select_field.choices)
        self.assertEqual(len(select_field.choices.split(',')), 4)