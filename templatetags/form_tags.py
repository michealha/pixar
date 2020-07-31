from django import template
from django.db import models
register = template.Library()

@register.filter
def field_type(bound_field):
    return bound_field.field.widget.__class__.__name__

@register.filter
def input_class(bound_field):
    css_class = ''
    if bound_field.form.is_bound:
        if bound_field.errors:
            css_class = 'is-invalid'
        elif field_type(bound_field) != 'PasswordInput':
            css_class = 'is-valid'
            
    return 'form-control {}'.format(css_class)

@register.filter
def format_size(size):
    label = ''
    gb = 1000000000
    mb = 1000000
    if size >= gb:
        s = float(size/gb)
        label = 'GB'
    else:
        s = float(size/mb)
        label = 'MB'

    return f'{round_of_the_size(s)} {label}'

def round_of_the_size(s):
    s = str(s).split('.')
    rd = s[1].strip()
    vr = rd[0]+rd[1]
    s = s[0]+"."+vr 
    return s

@register.filter
def format_title(title):
    if len(title) > 10:
        title = str(title)[:10]
        truncated = title + "...."
    else:
        truncated = title 
    return truncated 


@register.filter 
def filter_likes(likes):
    post_fix = ''
    if likes >= 1000000:
        post_fix = 'M'
        likes = int(likes/1000000)
    elif likes >= 1000:
        likes = int(likes/1000)
    post_fix = 'K'
    return f'{likes}{post_fix}'

@register.filter
def check_length(text):
    return len(str(text))





    

    