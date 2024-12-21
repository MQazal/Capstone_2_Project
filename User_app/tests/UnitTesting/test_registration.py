from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from User_app.models import Event, EventFormField, EventRegistration
from datetime import datetime, timedelta

class EventRegistrationProcessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.event = Event.objects.create(
            EventType="Workshop",
            EventTitle="Python Workshop",
            EventDescription="Advanced Python Topics",
            EventDate=datetime.now().date() + timedelta(days=15),
            EventTime=datetime.now().time(),
            EventCost="200 SAR",
            EventCapacity=50,
            current_participants=0
        )
        self.name_field = EventFormField.objects.create(
            event=self.event,
            field_name="Full Name",
            field_type="text",
            is_required=True
        )
        self.email_field = EventFormField.objects.create(
            event=self.event,
            field_name="Email",
            field_type="email",
            is_required=True
        )

    def test_registration_with_payment(self):
        self.client.login(username='testuser', password='testpass123')
        registration_data = {
            f'field_{self.name_field.id}': 'Test User',
            f'field_{self.email_field.id}': 'test@example.com',
            'payment_method': 'credit_card'
        }
        response = self.client.post(
            reverse('register_event', kwargs={'event_id': self.event.EventID}),
            data=registration_data
        )
        registration = EventRegistration.objects.first()
        self.assertEqual(registration.payment_status, 'pending')
        self.assertEqual(registration.payment_method, 'credit_card')
