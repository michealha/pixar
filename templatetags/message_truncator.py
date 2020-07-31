import re
from django import template
from datetime import date 
from django.utils import timezone

register = template.Library()

@register.filter
def truncate(text):
    if len(text) > 35:
        return f'{text[:35]}. . .'
    return text 

