from django.test import TestCase, Client
from django.urls import reverse
from datetime import datetime, timedelta
from User_app.models import Event

class DashboardFunctionalityTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Set up admin session
        session = self.client.session
        session['admin_logged_in'] = True
        session.save()

    def test_dashboard_access(self):
        """Test dashboard access control"""
        # Test with admin session
        response = self.client.get(reverse('Dashboard_Home'))
        self.assertEqual(response.status_code, 200)

        # Test without admin session
        session = self.client.session
        session['admin_logged_in'] = False
        session.save()
        response = self.client.get(reverse('Dashboard_Home'))
        self.assertNotEqual(response.status_code, 200)

    def test_event_management(self):
        """Test event management functionality"""
        # Create event
        event_data = {
            'EventType': 'Seminar',
            'EventTitle': 'Test Seminar',
            'EventDescription': 'Test Description',
            'EventDate': (datetime.now().date() + timedelta(days=20)).strftime('%Y-%m-%d'),
            'EventTime': '15:00',
            'EventCost': 'Free',
            'EventLocation': 'Test Location'
        }
        response = self.client.post(reverse('Create_Event'), data=event_data)
        event = Event.objects.first()
        
        # Update event
        event_data['EventTitle'] = 'Updated Seminar'
        response = self.client.post(
            reverse('Update_Event', kwargs={'pk': event.EventID}),
            data=event_data
        )
        updated_event = Event.objects.get(EventID=event.EventID)
        self.assertEqual(updated_event.EventTitle, 'Updated Seminar')

        # Delete event
        response = self.client.post(reverse('Delete_Event', kwargs={'pk': event.EventID}))
        self.assertEqual(Event.objects.count(), 0)