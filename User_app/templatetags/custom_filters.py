from django import template

register = template.Library()

@register.filter(name='get_dict_value')
def get_dict_value(registration_data, field):
    # Try to build the key as field_{id}
    field_key = f"field_{field.id}"
    
    # First try to get the value using the constructed key
    value = registration_data.get(field_key)
    
    if value is None:
        # If not found, try alternate ways to find the value
        # Try matching by field name
        for key, val in registration_data.items():
            if key == field.field_name.lower().replace(' ', '_'):
                return val
    
    return value if value is not None else ''