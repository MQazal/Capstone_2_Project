from django.contrib import admin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from .models import Event, EventFormField, EventRegistration
#import json

@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'get_formatted_data', 'created_at')
    readonly_fields = ('get_formatted_data', 'created_at')  # Add created_at as readonly
    fields = ('event', 'user', 'registration_data', 'created_at', 'get_formatted_data')  # Define fields to display

    def get_formatted_data(self, obj):
        try:
            data = obj.registration_data
            formatted_lines = []
            
            # Get the field names from EventFormField
            field_names = {
                f"field_{field.id}": field.field_name 
                for field in obj.event.form_fields.all()
            }
            
            # Format each field with its proper name
            for key, value in data.items():
                if key in field_names:
                    formatted_lines.append(f"{field_names[key]}: {value}")
                elif key == 'payment_method':
                    formatted_lines.append(f"Payment Method: {value}")
            
            return "\n".join(formatted_lines)
        except Exception:
            return "Error displaying data"
    get_formatted_data.short_description = 'Registration Data'

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('EventTitle', 'EventType', 'EventDate', 'EventCost', 'EventLocation')
    search_fields = ('EventTitle', 'EventType')
    list_filter = ('EventType', 'EventDate', 'form_configured')

@admin.register(EventFormField)
class EventFormFieldAdmin(admin.ModelAdmin):
    list_display = ('event', 'field_name', 'field_type', 'is_required')
    list_filter = ('field_type', 'is_required')
    search_fields = ('field_name', 'event__EventTitle')