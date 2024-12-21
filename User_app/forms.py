from django import forms
from django.core.exceptions import ValidationError
from .models import Event, EventRegistration

class SignupForm(forms.Form):
    username = forms.CharField(
        max_length=150, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={'required': 'Username is required'}
    )
    fname = forms.CharField(
        max_length=30, 
        label="First Name", 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={'required': 'First name is required'}
    )
    lname = forms.CharField(
        max_length=30, 
        label="Last Name", 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={'required': 'Last name is required'}
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        error_messages={'required': 'Email is required', 'invalid': 'Enter a valid email'}
    )
    pass1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}), 
        label="Password",
        error_messages={'required': 'Password is required'}
    )
    pass2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}), 
        label="Confirm Password",
        error_messages={'required': 'Confirm password is required'}
    )

    def clean(self):
        cleaned_data = super().clean()
        pass1 = cleaned_data.get('pass1')
        pass2 = cleaned_data.get('pass2')
        
        if pass1 and pass2 and pass1 != pass2:
            raise ValidationError("Passwords do not match!")
        
        return cleaned_data

class SigninForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    pass1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}), 
        label="Password",
        error_messages={'required': 'Password is required'}
    )

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['EventType', 'EventTitle', 'EventDescription', 
                'EventDate', 'EventTime', 'EventCost', 'EventCapacity', 'EventLocation']
    
    def clean_EventCost(self):
        cost = self.cleaned_data['EventCost'].strip()
        if cost.lower() == 'free':
            return 'Free'
        try:
            cost = ''.join(c for c in cost if c.isdigit() or c == '.')
            float_cost = float(cost)
            return f"{float_cost:.2f} SAR"
        except ValueError:
            raise forms.ValidationError("Please enter either 'Free' or a valid number")

class DynamicEventRegistrationForm(forms.Form):
    def __init__(self, event, user=None, *args, **kwargs):  # Add user parameter
        super().__init__(*args, **kwargs)
        
        # Add event-specific fields
        for field in event.form_fields.all():
            field_kwargs = {
                'label': field.field_name,
                'required': field.is_required,
                'widget': forms.TextInput(attrs={'class': 'form-control'})
            }
            
            if field.field_type == 'text':
                self.fields[f'field_{field.id}'] = forms.CharField(**field_kwargs)
            elif field.field_type == 'email':
                self.fields[f'field_{field.id}'] = forms.EmailField(
                    **field_kwargs,
                    initial=user.email if user else None,  # Set initial email
                    disabled=True  # Make it read-only
                )
            elif field.field_type == 'number':
                self.fields[f'field_{field.id}'] = forms.IntegerField(**field_kwargs)
            elif field.field_type == 'select':
                choices = [(c.strip(), c.strip()) for c in field.choices.split(',')]
                field_kwargs['widget'] = forms.Select(attrs={'class': 'form-control'})
                self.fields[f'field_{field.id}'] = forms.ChoiceField(choices=choices, **field_kwargs)