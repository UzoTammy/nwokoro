from typing import Optional

from django.db.models import F, QuerySet
from django.db.models.aggregates import Sum

from djmoney.money import Money

from .models import ExchangeRate, FinancialData


def get_value(instrument:QuerySet, _type:Optional[str]):

    """
        This function takes the database of a user's instruments,
        and aggregate them into their respective currencies
        :params
            - instrument: the active queryset of all instruments of a user
            - _type: the instrument type
        :result:
            - returns a list of Money objects in each currency
            - raise a ValueError if unacceptable option argument is given
    """
    
    totals = []
    if _type.lower() == 'investment':
            currencies = instrument.values_list('principal_currency', flat=True).distinct()
    elif _type.lower() == 'business' or _type.lower() == 'stock':
        currencies = instrument.values_list('unit_cost_currency', flat=True).distinct()
    elif _type.lower() == 'asset' or _type.lower() == 'saving':
        currencies = instrument.values_list('value_currency', flat=True).distinct()
    else:
        raise ValueError("Unacceptable instrument type argument")
        
    for currency in currencies:
        if _type.lower() == 'investment':
            raw_value = instrument.filter(principal_currency=currency).aggregate(Sum('principal'))['principal__sum']
        elif _type.lower() == 'business':
            raw_value = instrument.filter(unit_cost_currency=currency).annotate(value=F('shares')*F('unit_cost')).aggregate(Sum('value'))['value__sum']
        elif _type.lower() == 'stock':
            raw_value = instrument.filter(unit_cost_currency=currency).annotate(value=F('units')*F('unit_cost')).aggregate(Sum('value'))['value__sum']
        elif _type.lower() == 'asset' or _type.lower() == 'saving':
            raw_value = instrument.filter(value_currency=currency).aggregate(Sum('value'))['value__sum']
    
        totals.append(Money(raw_value, currency))
          
    return totals

def get_USD_value(instrument:QuerySet, _type:Optional[str]):
        
        """
            This function takes all instruments of a user in all currencies
            as stored, convert them to a uniform currency (USD) and sums them.
            :params
                - instrument is the various profit yielding asset of a user
                - type helps to identify the way to aggregate the instrument.
                Acceptable options are investment, business, stock, asset or saving
            :result
                - returns a Money object of the total sum of the given element
                - raise a ValueError if unacceptable option argument is given
        """    
        
        if _type.lower() == 'investment':
            currencies = instrument.values_list('principal_currency', flat=True).distinct()
        elif _type.lower() == 'business' or _type.lower() == 'stock':
            currencies = instrument.values_list('unit_cost_currency', flat=True).distinct()
        elif _type.lower() == 'asset' or _type.lower() == 'saving':
            currencies = instrument.values_list('value_currency', flat=True).distinct()
        else:
            raise ValueError("Unacceptable instrument type argument")
        
        total = 0
        for currency in currencies:
            if _type.lower() == 'investment':
                raw_value = instrument.filter(principal_currency=currency).aggregate(Sum('principal'))['principal__sum']
            elif _type.lower() == 'business':
                raw_value = instrument.filter(unit_cost_currency=currency).annotate(value=F('shares')*F('unit_cost')).aggregate(Sum('value'))['value__sum']
            elif _type.lower() == 'stock':
                raw_value = instrument.filter(unit_cost_currency=currency).annotate(value=F('units')*F('unit_cost')).aggregate(Sum('value'))['value__sum']
            elif _type.lower() == 'asset' or _type.lower() == 'saving':
                raw_value = instrument.filter(value_currency=currency).aggregate(Sum('value'))['value__sum']

            value = float(raw_value)/ExchangeRate.objects.get(target_currency=currency).rate
            total += value
            
        return Money(total, 'USD')

def naira_valuation():
    """
        The devaluation of naira since beginning of the year
    """
    fd = FinancialData.objects.exclude(exchange_rate=None)
    date = fd.earliest('date').date
    value = fd.earliest('date').exchange_rate['NGN'] - fd.latest('date').exchange_rate['NGN']
    tag = 'lost' if value < 0 else 'gained'
    return Money(round(abs(value), 2), 'NGN'), tag, date.strftime('%d %b, %Y') #{'old_value': fd.earliest('date').exchange_rate['NGN'], 'new_value': fd.latest('date').exchange_rate['NGN']}