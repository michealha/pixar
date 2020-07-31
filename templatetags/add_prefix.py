from django import template

register = template.Library()

@register.filter
def add_prefix(username):
    prefix = ''
    if username.endswith('s'):
        prefix = "'"
    else:
        prefix = "'s"

    return f'{username}{prefix}'
