from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter(name='scalar_value')
def absolute(value):
    try:
        return abs(value)
    except (ValueError, TypeError):
        return None

@register.filter(name='divide')
def divide(numerator, denominator):
    try:
        return int(numerator/denominator)
    except (ValueError, TypeError, ZeroDivisionError):
        return None

