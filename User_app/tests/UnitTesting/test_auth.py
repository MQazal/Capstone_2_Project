from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from User_app.forms import SignupForm

class UserAuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('signup')
        self.signin_url = reverse('signin')
        self.home_url = reverse('home')

    def test_signup_form_validation(self):
        form_data = {
            'username': 'testuser',
            'fname': 'Test',
            'lname': 'User',
            'email': 'test@example.com',
            'pass1': 'testpass123',
            'pass2': 'testpass123'
        }
        form = SignupForm(data=form_data)
        self.assertTrue(form.is_valid())

        form_data['pass2'] = 'wrongpass'
        form = SignupForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_signin_process(self):
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        response = self.client.post(self.signin_url, {
            'email': 'test@example.com',
            'pass1': 'testpass123'
        })
        self.assertRedirects(response, self.home_url)

        response = self.client.post(self.signin_url, {
            'email': 'test@example.com',
            'pass1': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)