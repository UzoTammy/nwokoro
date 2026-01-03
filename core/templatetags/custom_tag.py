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
    
@register.filter
def get_item(list_obj, index):

    if type(list_obj) is not list:
        list_obj = list(list_obj)
    try:
        return list_obj[index]
    except (IndexError, TypeError):
        return None
    
@register.filter
def to_usd(value):
    from networth.tools import exchange_rate
    rate_func = exchange_rate(value.currency) if value.currency != 'USD' else (1,)
    try:
        return f'${(value/rate_func[0]):,.2f}'
    except (ValueError, TypeError, ZeroDivisionError):
        return None
    

    
