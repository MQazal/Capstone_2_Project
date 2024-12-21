from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from User_app.models import Event, EventFormField, EventRegistration
from datetime import datetime, timedelta

class EventManagementFlowTests(TestCase):
    """Integration tests for the complete event management process"""
    
    def setUp(self):
        self.client = Client()
        # Set up admin session
        session = self.client.session
        session['admin_logged_in'] = True
        session.save()
        
        # Initialize test data
        self.event_data = {
            'EventType': 'Conference',
            'EventTitle': 'Tech Summit 2024',
            'EventDescription': 'Annual Technology Conference',
            'EventDate': (datetime.now().date() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'EventTime': '14:00',
            'EventCost': '500 SAR',
            'EventCapacity': 100,
            'EventLocation': 'https://maps.google.com/test-venue'
        }

    def test_complete_event_management_flow(self):
        """Test the entire event management process"""
        
        # 1. Admin Dashboard Access
        response = self.client.get(reverse('Dashboard_Home'))
        self.assertEqual(response.status_code, 200)
        
        # 2. Create Event
        create_response = self.client.post(
            reverse('Create_Event'),
            data=self.event_data
        )
        self.assertEqual(Event.objects.count(), 1)
        event = Event.objects.first()
        
        # 3. Configure Registration Form
        form_fields = [
            {
                'field_name': 'Company Name',
                'field_type': 'text',
                'is_required': True
            },
            {
                'field_name': 'Job Title',
                'field_type': 'text',
                'is_required': True
            },
            {
                'field_name': 'Dietary Preferences',
                'field_type': 'select',
                'is_required': True,
                'choices': 'Vegetarian,Non-Vegetarian,Vegan'
            }
        ]
        
        for field_data in form_fields:
            field_response = self.client.post(
                reverse('form_manager', kwargs={'event_id': event.EventID}),
                {'action': 'add_field', **field_data}
            )
        
        # 4. Save Form Configuration
        save_form_response = self.client.post(
            reverse('form_manager', kwargs={'event_id': event.EventID}),
            {'action': 'save_form'}
        )
        event.refresh_from_db()
        self.assertTrue(event.form_configured)
        
        # 5. Update Event
        updated_data = self.event_data.copy()
        updated_data['EventTitle'] = 'Updated Tech Summit 2024'
        update_response = self.client.post(
            reverse('Update_Event', kwargs={'pk': event.EventID}),
            data=updated_data
        )
        event.refresh_from_db()
        self.assertEqual(event.EventTitle, 'Updated Tech Summit 2024')
        
        # 6. Verify Event Listing
        list_response = self.client.get(reverse('Dashboard_Home'))
        self.assertContains(list_response, 'Updated Tech Summit 2024')
        
        # 7. Event Deletion
        delete_response = self.client.post(
            reverse('Delete_Event', kwargs={'pk': event.EventID})
        )
        self.assertEqual(Event.objects.count(), 0)