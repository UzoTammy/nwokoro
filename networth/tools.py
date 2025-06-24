import datetime
from typing import Optional, List

from django.db.models import F, QuerySet, Q
from django.db.models.aggregates import Sum

from djmoney.money import Money

from .models import ExchangeRate, FinancialData, Investment


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


def ytd_roi(owner, year:Optional[int]=None)->List[dict]:
    """
        This function takes a year and returns investment
        yields according to the various currencies
        :prams 
            - year
        :return
            - list of dictionaries.Each dictionary represents
            a group of investments in one currency
    """
    if year is None:
        year = datetime.datetime.now().year
    # investments = Investment.objects.filter(Q(start_date__year=year)|Q(start_date__year=year-1))
    investments = Investment.objects.filter(owner=owner)
    pks = [investment.pk for investment in investments if investment.maturity().year == year]
    investments = Investment.objects.filter(pk__in=pks)
    currencies = investments.values_list('principal_currency', flat=True).distinct()
    store = list()
    for currency in currencies:
        store.append(investments.filter(principal_currency=currency))
    
    summation = list()
    for qs in store:
        principal = roi = Money(0, qs.first().principal.currency)
        for investment in qs:
            principal += investment.principal
            roi += investment.roi()
        summation.append({'principal': principal, 'roi': roi, 'percent': round(100*roi/principal, 2)})
    return summation


def investments_by_holder(owner):
    stack = list()
    active_investments = Investment.objects.filter(is_active=True).filter(owner=owner)
    holders = active_investments.values_list('holder', flat=True).distinct()
    investments = list(active_investments.filter(holder=holder) for holder in holders)

    for qs in investments:
        exch = ExchangeRate.objects.all()
        holder = qs.first().holder
        store = list()
        for obj in qs:
            data = {"value": obj.principal, 'maturity': obj.maturity()}
            rate = exch.get(target_currency=obj.principal.currency).rate
            value_in_usd = float(obj.principal.amount)/rate
            roi_in_usd = float(obj.roi().amount)/rate
            data['value_in_usd'] = Money(value_in_usd, 'USD')
            data['roi_in_usd'] = Money(roi_in_usd, 'USD')
            store.append(data)
        holders_data = {holder: store}
        stack.append(holders_data)
    return stack