import datetime
from decimal import Decimal
from typing import Optional, List

from django.core.mail import EmailMultiAlternatives
from django.db.models import F, QuerySet
from django.db.models.aggregates import Sum
from django.http import HttpResponse
from django.template.loader import render_to_string

from djmoney.money import Money
from babel.numbers import format_currency

from .models import (ExchangeRate, Investment, Saving, Stock, Business, FixedAsset, BorrowedFund, FinancialData)


class FinancialReport:

    def __init__(self, savings, investments, stocks, business, fixed_asset, liability):
        self.savings = savings
        self.investments = investments
        self.stocks = stocks
        self.business = business
        self.fixed_asset = fixed_asset
        self.liability = liability

    @staticmethod
    def convert_to_base(money_list):
        result = list()
        for money in money_list:
            exchange = ExchangeRate.objects.filter(
                target_currency=money.currency)
            if exchange.exists():
                result.append(Money(
                    money.amount/Decimal(exchange.first().rate), exchange.first().base_currency))
        return sum(result) if result else Money(0, 'USD')

    def get_owner(self):
        # string
        return self.savings.first().owner

    def get_countries(self):
        # based on the premise that all host country must have savings account
        countries = list(self.savings.values_list(
            'host_country', flat=True).distinct())
        return countries

    def get_saving_total(self, country=None):
        savings = self.savings.filter(host_country=country) if country else self.savings
        return get_USD_value(savings, 'saving')

    def get_investment_total(self, country=None):
        investments = self.investments.filter(host_country=country) if country else self.investments
        return get_USD_value(investments, 'investment')

    def get_stock_total(self, country=None):
        stocks = self.stocks.filter(host_country=country) if country else self.stocks
        return get_USD_value(stocks, 'stock')

    def get_business_total(self, country=None):
        business = self.business.filter(host_country=country) if country else self.business
        return get_USD_value(business, 'business')

    def get_fixed_asset_total(self, country=None):
        fixed_asset = self.fixed_asset.filter(host_country=country) if country else self.fixed_asset
        return get_USD_value(fixed_asset, 'asset')

    def get_liability_total(self, country=None):
        liability = self.liability.filter(host_country=country) if country else self.liability

        total = list()
        if self.liability.exists():
            currencies = liability.values_list(
                'borrowed_amount_currency', flat=True).distinct().order_by('borrowed_amount_currency')
            if currencies.exists():
                for currency in currencies:
                    liabilities = liability.filter(borrowed_amount_currency=currency).aggregate(Sum('settlement_amount'))['settlement_amount__sum']
                    total.append(Money(liabilities, currency))
            
        return FinancialReport.convert_to_base(total)

    def getNetworth(self, country=None):

        return sum(
            (self.get_investment_total(country),
            self.get_saving_total(country),
            self.get_stock_total(country),
            self.get_business_total(country),
            self.get_fixed_asset_total(country)
            -self.get_liability_total(country))
        )

    def get_roi(self):
        return FinancialReport.convert_to_base([x.roi() for x in self.investments])

    def get_daily_roi(self):
        return FinancialReport.convert_to_base([x.daily_roi() for x in self.investments])

    def get_present_roi(self):
        return FinancialReport.convert_to_base([x.present_roi() for x in self.investments])

    def country_networth(self):
        networth = dict()
        countries = self.get_countries() # CA, NG, US
        for country in countries:
            networth[country] = float(round(self.getNetworth(country).amount, 2))
        return networth

    def send_email(self):
        from_email = "no-reply@chores.com"

        subject = "Financial Data Saved to Database"
        to_email = [self.get_owner().email]

        fd = FinancialData.objects.order_by('-date')[1] # previous latest

        html_content = render_to_string('networth/mails/financial_report.html', {
            'networth': self.getNetworth(),
            'savings': self.get_saving_total(),
            'investments': self.get_investment_total(),
            'stocks': self.get_stock_total(),
            'business': self.get_business_total(),
            'fixed_asset': self.get_fixed_asset_total(),
            'liability': self.get_liability_total(),
            'roi': self.get_roi(),
            'daily_roi': self.get_daily_roi(),
            'present_roi': self.get_present_roi(),
            'prev_networth': fd.networth,
            'change_in_networth': self.getNetworth() - fd.networth(),
            'exchange_rate': f"{format_currency(fd.exchange_rate['NGN']/fd.exchange_rate['CAD'], currency='NGN', locale='en_US')}/CA$"
        })

        # Create the email message
        msg = EmailMultiAlternatives(subject, "plain text", from_email, to_email,
                                     headers={"Reply-To": "nwokorouzo@gmail.com"},)
        
        msg.attach_alternative(html_content, "text/html")

        try:
            msg.send()
        except Exception as e:
            return HttpResponse(f"Failed to send email: {e}")

    def save_report(self):

        FinancialData.objects.create(
            owner=self.get_owner(), # string
            worth=self.getNetworth(),
            savings=self.get_saving_total(),
            investment=self.get_investment_total(),
            stock=self.get_stock_total(),
            business=self.get_business_total(),
            fixed_asset=self.get_fixed_asset_total(),
            liability=self.get_liability_total(),
            roi=self.get_roi(),
            daily_roi=self.get_daily_roi(),
            present_roi=self.get_present_roi(),
            networth_by_country=self.country_networth()
        )

def get_user_finances(username: str)->Optional[FinancialReport]:
    savings = Saving.objects.filter(owner__username=username)
    if savings.exists():
        investments = Investment.objects.filter(is_active=True).filter(owner__username=username)
        stocks = Stock.objects.filter(owner__username=username)
        business = Business.objects.filter(owner__username=username)
        fixed_asset = FixedAsset.objects.filter(owner__username=username)
        liability = BorrowedFund.objects.filter(owner__username=username)
        fr = FinancialReport(savings, investments, stocks, business, fixed_asset, liability)
        return fr
    
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
        This function takes a year of a user and returns investment
        yields according to the various currencies
        :params 
            - owner
            - year
        :return
            - dict of dict
    """
    if year is None:
        year = datetime.datetime.now().year

    investments = Investment.objects.filter(owner=owner)
    pks = [investment.pk for investment in investments if investment.maturity().year == year]
    investments = Investment.objects.filter(pk__in=pks)
    currencies = ExchangeRate.objects.values_list('target_currency', flat=True)
    store = list()
    for currency in currencies:
        store.append(investments.filter(principal_currency=currency))
     
    stack = dict()
    for qs, currency in zip(store, currencies):
        if qs.exists():
            principal = roi = Money(0, currency)
            for investment in qs:
                principal += investment.principal
                roi += investment.roi()
            stack[currency] = {'principal': principal, 'roi': roi, 'percent': round(100*roi/principal, 2)}
        else:
            stack[currency] = {'principal': Money(0, currency), 'roi': Money(0, currency), 'percent': 0.0} 
    return stack

def investments_by_holder(owner):
    stack = list()
    active_investments = Investment.objects.filter(is_active=True).filter(owner=owner)
    holders = active_investments.values_list('holder', flat=True).distinct()
    investments = list(active_investments.filter(holder=holder) for holder in holders)

    for qs in investments:
        exch = ExchangeRate.objects.all()
        holder = qs.first().holder
        store = list()
        # totals = list()
        value_total = roi_total = Money(0, 'USD')
        for obj in qs:
            data = {"value": obj.principal, 'maturity': obj.maturity()}
            rate = exch.get(target_currency=obj.principal.currency).rate
            value_in_usd = float(obj.principal.amount)/rate
            roi_in_usd = float(obj.roi().amount)/rate
            data['value_in_usd'] = Money(value_in_usd, 'USD')
            data['roi_in_usd'] = Money(roi_in_usd, 'USD')
            value_total += Money(value_in_usd, 'USD')
            roi_total += Money(roi_in_usd, 'USD')
            store.append(data)
        holders_data = {holder: (store, (value_total, roi_total))}
        # [{holder: ([], (value total, roi total))}]
        stack.append(holders_data)
    return stack