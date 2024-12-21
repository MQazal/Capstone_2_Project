from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from User_app.models import Event, EventFormField, EventRegistration
from datetime import datetime, timedelta

class EventRegistrationFlowTests(TestCase):
    """Integration tests for the complete event registration process"""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create test event
        self.event = Event.objects.create(
            EventType="Conference",
            EventTitle="Tech Conference 2024",
            EventDescription="Annual Technology Conference",
            EventDate=datetime.now().date() + timedelta(days=30),
            EventTime=datetime.now().time(),
            EventCost="500 SAR",
            EventCapacity=100,
            EventLocation="https://maps.google.com/test-venue"
        )
        
        # Create form fields
        self.required_fields = [
            ("Full Name", "text"),
            ("Email", "email"),
            ("Phone", "text"),
            ("Gender", "select", "Male,Female")
        ]
        
        self.form_fields = []
        for field_data in self.required_fields:
            field_kwargs = {
                'event': self.event,
                'field_name': field_data[0],
                'field_type': field_data[1],
                'is_required': True
            }
            if len(field_data) > 2:
                field_kwargs['choices'] = field_data[2]
            
            self.form_fields.append(
                EventFormField.objects.create(**field_kwargs)
            )
        
        self.client = Client()

    def test_complete_registration_flow(self):
        """Test the entire registration process from login to confirmation"""
        
        # 1. User login
        login_successful = self.client.login(
            username='testuser',
            password='testpass123'
        )
        self.assertTrue(login_successful)
        
        # 2. Browse events
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tech Conference 2024")
        
        # 3. Search for event
        search_response = self.client.get(
            reverse('search_events'),
            {'event_type': 'Conference'}
        )
        self.assertEqual(search_response.status_code, 200)
        self.assertContains(search_response, "Tech Conference 2024")
        
        # 4. Access registration form
        form_response = self.client.get(
            reverse('register_event', kwargs={'event_id': self.event.EventID})
        )
        self.assertEqual(form_response.status_code, 200)
        
        # 5. Submit registration
        registration_data = {
            f'field_{self.form_fields[0].id}': 'Test User',
            f'field_{self.form_fields[1].id}': 'test@example.com',
            f'field_{self.form_fields[2].id}': '+1234567890',
            f'field_{self.form_fields[3].id}': 'Male',
            'payment_method': 'credit_card'
        }
        
        register_response = self.client.post(
            reverse('register_event', kwargs={'event_id': self.event.EventID}),
            data=registration_data
        )
        
        # 6. Verify registration success
        self.assertEqual(EventRegistration.objects.count(), 1)
        registration = EventRegistration.objects.first()
        
        # 7. Check confirmation page
        confirmation_response = self.client.get(
            reverse('registration_confirmation', 
                   kwargs={'registration_id': registration.id})
        )
        self.assertEqual(confirmation_response.status_code, 200)
        self.assertContains(confirmation_response, "Tech Conference 2024")
        
        # 8. Verify user account shows registration
        account_response = self.client.get(reverse('user_account'))
        self.assertEqual(account_response.status_code, 200)
        self.assertContains(account_response, "Tech Conference 2024")

    def test_registration_capacity_handling(self):
        """Test registration flow when event reaches capacity"""
        self.client.login(username='testuser', password='testpass123')
        
        # Fill event to capacity
        self.event.current_participants = self.event.EventCapacity
        self.event.save()
        
        # Attempt registration
        registration_data = {
            f'field_{self.form_fields[0].id}': 'Test User',
            f'field_{self.form_fields[1].id}': 'test@example.com',
            f'field_{self.form_fields[2].id}': '+1234567890',
            f'field_{self.form_fields[3].id}': 'Male'
        }
        
        response = self.client.post(
            reverse('register_event', kwargs={'event_id': self.event.EventID}),
            data=registration_data
        )
        
        # Verify registration was prevented
        self.assertEqual(EventRegistration.objects.count(), 0)
        self.assertContains(response, "event is already full", status_code=200)