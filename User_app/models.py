from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Event(models.Model):
    EventID = models.AutoField(primary_key=True)
    EventType = models.CharField(max_length=50)
    EventTitle = models.CharField(max_length=70)
    EventDescription = models.TextField()
    EventDate = models.DateField()
    EventTime = models.TimeField()
    EventCost = models.CharField(max_length=20, default='Free')
    EventLocation = models.CharField(max_length=70)
    EventCapacity = models.PositiveIntegerField(null=True, blank=True)
    current_participants = models.PositiveIntegerField(default=0)
    form_configured = models.BooleanField(default=False)

    def __str__(self):
        return self.EventTitle

    def save(self, *args, **kwargs):
        if self.EventCapacity == '':
            self.EventCapacity = None
        super().save(*args, **kwargs)
    
    def is_full(self):
        if self.EventCapacity is None:  # Unlimited capacity
            return False
        return self.current_participants >= self.EventCapacity
    
    def add_participant(self):
        if not self.is_full():
            self.current_participants += 1
            self.save()
            return True
        return False
    
    def remove_participant(self):
        if self.current_participants > 0:
            self.current_participants -= 1
            self.save()
            return True
        return False


class EventFormField(models.Model):
    FIELD_TYPES = [
        ('text', 'Text Input'),
        ('email', 'Email'),
        ('number', 'Number'),
        ('select', 'Dropdown'),
        ('date', 'Date'),
        ('time', 'Time'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='form_fields')
    field_name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    is_required = models.BooleanField(default=True)
    choices = models.TextField(blank=True, null=True, help_text="Comma-separated choices for dropdown")

    def __str__(self):
        return f"{self.event.EventTitle} - {self.field_name}"

class EventRegistration(models.Model):
    PAYMENT_METHODS = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('cash', 'Cash'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    registration_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(
        max_length=20, 
        choices=PAYMENT_METHODS,
        null=True,
        blank=True
    )
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('not_required', 'Not Required'),
        ],
        default='not_required'
    )

    def __str__(self):
        return f"{self.user.username} - {self.event.EventTitle}"

    class Meta:
        unique_together = ['event', 'user']

    def save(self, *args, **kwargs):
        # Check if this is a new registration
        is_new = self._state.adding
        
        if is_new and self.event.is_full():
            raise ValidationError("This event has reached its capacity.")
            
        if self.event.EventCost.lower() == 'free':
            self.payment_status = 'not_required'
            self.payment_method = None
        elif not self.payment_status:
            self.payment_status = 'pending'
            
        super().save(*args, **kwargs)
        
        # Update participant count
        if is_new:
            self.event.add_participant()