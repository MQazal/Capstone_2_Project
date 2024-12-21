from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from User_app.models import Event, EventFormField, EventRegistration
from datetime import datetime, timedelta


class SearchAndBookingFlowTests(TestCase):
    """Integration tests for search and booking workflow"""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create multiple test events
        self.events = [
            Event.objects.create(
                EventType="Conference",
                EventTitle=f"Conference {i}",
                EventDescription=f"Test Conference {i}",
                EventDate=datetime.now().date() + timedelta(days=30+i),
                EventTime=datetime.now().time(),
                EventCost="500 SAR" if i % 2 == 0 else "Free",
                EventCapacity=100,
                EventLocation=f"https://maps.google.com/venue{i}"
            ) for i in range(1, 4)
        ]
        
        # Add form fields to each event
        for event in self.events:
            EventFormField.objects.create(
                event=event,
                field_name="Full Name",
                field_type="text",
                is_required=True
            )
        
        self.client = Client()

    def test_search_and_booking_workflow(self):
        """Test complete search and booking process"""
        
        # 1. User Login
        self.client.login(username='testuser', password='testpass123')
        
        # 2. Search Events
        search_response = self.client.get(
            reverse('search_events'),
            {'event_type': 'Conference'}
        )
        self.assertEqual(search_response.status_code, 200)
        for event in self.events:
            self.assertContains(search_response, event.EventTitle)
        
        # 3. Filter Free Events
        free_events = [e for e in self.events if e.EventCost == "Free"]
        self.assertTrue(len(free_events) > 0)
        
        # 4. Select and Book Free Event
        free_event = free_events[0]
        registration_data = {
            f'field_{free_event.form_fields.first().id}': 'Test User'
        }
        
        book_response = self.client.post(
            reverse('register_event', kwargs={'event_id': free_event.EventID}),
            data=registration_data
        )
        
        # 5. Verify Registration
        registration = EventRegistration.objects.filter(
            event=free_event,
            user=self.user
        ).first()
        self.assertIsNotNone(registration)
        self.assertEqual(registration.payment_status, 'not_required')
        
        # 6. Check User's Registrations
        account_response = self.client.get(reverse('user_account'))
        self.assertContains(account_response, free_event.EventTitle)

    def test_search_filters_and_pagination(self):
        """Test search functionality with filters and pagination"""
        
        # Test type filter
        response = self.client.get(
            reverse('search_events'),
            {'event_type': 'Conference'}
        )
        self.assertEqual(len(response.context['events']), 3)
        
        # Test cost filter
        free_response = self.client.get(
            reverse('search_events'),
            {'event_type': 'Conference', 'cost': 'Free'}
        )
        paid_events = [e for e in self.events if e.EventCost != "Free"]
        for event in paid_events:
            self.assertNotContains(free_response, event.EventTitle)