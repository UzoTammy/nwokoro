import datetime
import calendar
from decimal import Decimal
from itertools import chain
from typing import Optional, List, Literal
from dateutil.relativedelta import relativedelta

from django.core.mail import EmailMultiAlternatives
from django.db.models import F, QuerySet, Value, Avg
from django.db.models.aggregates import Sum
from django.http import HttpResponse
from django.template.loader import render_to_string

from djmoney.money import Money
from babel.numbers import format_currency

from account.models import User
from .models import (ExchangeRate, Investment, Saving, Stock, Business, FixedAsset, 
                     BorrowedFund, FinancialData, InvestmentTransaction, BusinessTransaction,
                     StockTransaction)

class Tax:
    nta2025_bands = [(800_000, 0), (2_200_000, .15), (9_000_000, .18), (13_000_000, .21), (25_000_000, .23), (50_000_0000, .25)]
    
    def __init__(self, income:float, rent:float=0):
        self.income = income
        self.rent = rent

    def _rent_relief(self, rent):
        relief = .3 * rent
        if relief > 500_000:
            return 500_000
        return relief

    def calculate_nigerian_income_tax(self, income:float, rent:float=0):
        income -= self._rent_relief(rent)
        payable = 0
        i = 0
        while income > 0:
            if income >= Tax.nta2025_bands[i][0]:
                payable += Tax.nta2025_bands[i][0] * Tax.nta2025_bands[i][1]
            else:
                payable += income * Tax.nta2025_bands[i][1]
            income -= Tax.nta2025_bands[i][0]
            i += 1
            
        return payable
            
class FinancialReport:

    def __init__(self, savings, investments, stocks, business, fixed_asset, liability):
        self.savings=savings
        self.investments=investments
        self.stocks=stocks
        self.business=business
        self.fixed_asset=fixed_asset
        self.liability=liability

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
            'change_in_networth': self.getNetworth() - fd.__networth(),
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
    
def exchange_rate(of:str, to:str=None):
    target = ExchangeRate.objects.filter(target_currency=of)
    if to is None:
        to = 'USD'
    if target.exists():
        target_rate = target.get().rate
        base = ExchangeRate.objects.filter(target_currency=to)
        if not base.exists():
            return None
        base_rate = base.get().rate
        rate = target_rate/base_rate
        return Money(rate, of), target.get().updated_at

def get_assets_liabilities(owner):
    """queryset of active assets of current logged-in user"""
    investments = Investment.objects.filter(is_active=True).filter(owner=owner)
    stocks = Stock.objects.filter(owner=owner)
    savings = Saving.objects.filter(owner=owner)
    business = Business.objects.filter(owner=owner).filter(is_active=True)
    fixed_asset = FixedAsset.objects.filter(owner=owner)
    liabilities = BorrowedFund.objects.filter(owner=owner)
    return {'investments': investments, 'stocks': stocks, 'savings': savings, 'business': business,
            'fixed_asset': fixed_asset, 'liabilities': liabilities}

def get_user_finances(username: str)->Optional[FinancialReport]:
    savings = Saving.objects.filter(owner__username=username).filter(value__gt=0)
    if savings.exists():
        # investments that are active
        investments = Investment.objects.filter(is_active=True).filter(owner__username=username)
        # Stock that exist and not sold: units > 0 or do not exist
        stocks = Stock.objects.filter(owner__username=username).filter(units__gt=0)
        business = Business.objects.filter(owner__username=username).filter(is_active=True)
        fixed_asset = FixedAsset.objects.filter(owner__username=username).filter(is_active=True)
        # when balance amount is 
        liability = BorrowedFund.objects.filter(owner__username=username).filter(balance_amount__gt=0)
        networth = FinancialReport(savings, investments, stocks, business, fixed_asset, liability)
        return networth
    
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
    elif _type.lower() == 'liability':
        currencies = instrument.values_list('settlement_amount_currency', flat=True).distinct()
    
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
        elif _type.lower() == 'liability':
            raw_value = instrument.filter(settlement_amount_currency=currency).aggregate(Sum('settlement_amount'))['settlement_amount__sum']
    
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

def valuation(currency):
    """
        Currency valuation since beginning of the year
    """
    fd = FinancialData.objects.exclude(exchange_rate=None)
    date = fd.earliest('date').date
    value = fd.earliest('date').exchange_rate[currency] - fd.latest('date').exchange_rate[currency]
    tag = 'lost' if value < 0 else 'gained'
    return Money(round(abs(value), 2), currency), tag, date.strftime('%d %b, %Y') #{'old_value': fd.earliest('date').exchange_rate['NGN'], 'new_value': fd.latest('date').exchange_rate['NGN']}

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
            stack[currency] = {'principal': principal, 'roi': roi, 'percent': round(100*roi/principal, 2), 'roi_usd': Money(roi.amount/exchange_rate(roi.currency)[0].amount, 'USD')}
        else:
            stack[currency] = {'principal': Money(0, currency), 'roi': Money(0, currency), 'percent': 0.0, 'roi_usd': Money(0, 'USD')} 
    
    return stack

def last_3_month_roi():
    today = datetime.date.today()
    date = datetime.date(today.year, today.month, 1)
    dates = (
        date - relativedelta(months=3),
        date - relativedelta(months=2),
        date - relativedelta(months=1)
    )
    y_axis, x_axis = list(), list()
    for date in dates:
        financial = FinancialData.objects.filter(date__year=date.year).filter(date__month=date.month)
        financial = financial.aggregate(Avg('roi'))['roi__avg'] if financial.exists() else Decimal('0')
        y_axis.append(financial)
        x_axis.append(date.strftime('%b'))
    return x_axis, y_axis

def current_year_roi(owner):

    today = datetime.date.today()
    year = today.year
    month = today.month

    completed_investments = InvestmentTransaction.objects.filter(investment__owner=owner).filter(transaction_type='DR').filter(timestamp__year=year)
    data = list()
    if completed_investments.exists():
        for i in range(1, month+1):
            investments = completed_investments.filter(timestamp__month=i)
            if investments.exists():
                total = Money(0, 'USD')
                for transaction in investments:
                    earned = transaction.amount - transaction.investment.principal
                    earned_usd = Money(earned/exchange_rate(earned.currency)[0], 'USD')
                    total += earned_usd
                data.append({'month': calendar.month_name[i], 'amount': total})
    return data

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

def get_transactions(*transactions, period:Literal['recent','year','all']='recent'):
     
    bucket = list()   
    for transaction in transactions:
        qs = transaction.objects.only('timestamp', 'amount_currency', 'amount')
        action = qs.model.__name__[:-11]
        qss = qs.annotate(action=Value(action)).values_list('action', 'timestamp__date', 'amount_currency', 'amount')
        qss = list((item[0], item[1], f'{item[2]}{item[3]:,.2f}') for item in qss)
        bucket.append(qss)
    chained_bucket = chain(*bucket)
    sorted_bucket = sorted(chained_bucket, key=lambda x:x[1], reverse=True)
    if period == 'recent':
        sorted_bucket = sorted_bucket[:6]
    elif period == 'year':
        year = datetime.date.today().year
        sorted_bucket = [ t for t in sorted_bucket if t[1].year==year ]
    
    return sorted_bucket

def networth_ratio(owner, country, currency, base_currency='USD'):
    """
        To compare networth in a country's local currency to the networth
        in US dollars in the same country.
    """
    result = list()
    for cur in (currency, base_currency):
        saving = Saving.objects.filter(owner=owner).filter(host_country=country).filter(value_currency=cur)
        total_value = saving.aggregate(Sum('value'))['value__sum'] if saving.exists() else Decimal('0')
        stack = [total_value]
        
        fixed = FixedAsset.objects.filter(owner=owner).filter(host_country=country).filter(value_currency=cur)
        total_value = fixed.aggregate(Sum('value'))['value__sum'] if fixed.exists() else Decimal('0')
        stack.append(total_value)

        invest = Investment.objects.filter(owner=owner).filter(host_country=country).filter(principal_currency=cur).filter(is_active=True)
        total_value = invest.aggregate(Sum('principal'))['principal__sum'] if invest.exists() else Decimal('0')
        stack.append(total_value)

        biz = Business.objects.filter(owner=owner).filter(host_country=country).filter(unit_cost_currency=cur).filter(is_active=True)
        total_value = biz.annotate(val=F('shares')*F('unit_cost')).aggregate(Sum('val'))['val__sum'] if biz.exists() else Decimal('0')
        stack.append(total_value)

        stock = Stock.objects.filter(owner=owner).filter(host_country=country).filter(unit_cost_currency=cur)
        total_value = stock.annotate(val=F('units')*F('unit_cost')).aggregate(Sum('val'))['val__sum'] if stock.exists() else Decimal('0')
        stack.append(total_value)

        total_value = sum(stack) 
        result.append(total_value)

        exchange_rate = ExchangeRate.objects.get(target_currency=currency).rate

    result[0] = Money(round(result[0]/Decimal(exchange_rate), 2), base_currency)
    result[1] = Money(round(result[1], 2), base_currency)
    if result[1] > Money(0, base_currency):
        result.append(result[0]/result[1])
    else:
        return {'country': country}
    return {'country': country, 'currency': result[0], 'base_currency': base_currency ,'base_value': result[1], 'ratio': round(result[2], 2)}

def number_of_instruments(username):
    "Assets with potentials to generate wealth"
    fixed = FixedAsset.objects.filter(owner__username=username).filter(value__gt=0).count()
    invest = Investment.objects.filter(owner__username=username).filter(is_active=True).count()
    biz = Business.objects.filter(owner__username=username).filter(is_active=True).count()
    stock = Stock.objects.filter(owner__username=username).filter(units__gt=0).count()
    return sum([fixed, invest, biz, stock])

def number_of_assets(username):
    savings = Saving.objects.filter(owner__username=username).filter(value__gt=0).count()
    return savings + number_of_instruments(username)

def set_roi(target: Money):
    year = datetime.date.today().year
    days = 366 if calendar.isleap(year) else 365
    daily = target.amount/days
    return Money(daily, 'USD')

def get_year_financial(owner:User, year:int=None):
    if year is None:
        year = datetime.date.today().year
    qs = FinancialData.objects.filter(owner=owner).filter(date__year=year).order_by('date')
    return qs

def networth_by_currency(currency, owner):
    """
        User's networth by currency
    """
    
    # filter the database for the queryset
    savings = Saving.objects.filter(owner=owner).filter(value_currency=currency)
    investments = Investment.objects.filter(owner=owner).filter(is_active=True).filter(principal_currency=currency)
    stocks = Stock.objects.filter(owner=owner).filter(unit_cost_currency=currency)
    business = Business.objects.filter(owner=owner).filter(unit_cost_currency=currency).filter(is_active=True)
    fixed_asset = FixedAsset.objects.filter(owner=owner).filter(value_currency=currency)
    liability = BorrowedFund.objects.filter(owner=owner).filter(settlement_amount_currency=currency).filter(is_active=True)
    
    # get the aggregate
    saving_amount = savings.aggregate(Sum('value'))['value__sum'] if savings.exists() else Decimal('0')
    investment_amount = investments.aggregate(Sum('principal'))['principal__sum'] if investments.exists() else Decimal('0')
    stock_amount = stocks.annotate(value=F('unit_cost')*F('units')).aggregate(Sum('value'))['value__sum'] if stocks.exists() else Decimal('0')      
    business_amount = business.annotate(value=F('unit_cost')*F('shares')).aggregate(Sum('value'))['value__sum'] if business.exists() else Decimal('0')
    fixed_asset_amount = fixed_asset.aggregate(Sum('value'))['value__sum'] if fixed_asset.exists() else Decimal('0')
    liability_amount = liability.aggregate(Sum('settlement_amount'))['settlement_amount__sum'] if liability.exists() else Decimal('0')

    total = saving_amount + investment_amount + stock_amount + business_amount + fixed_asset_amount - liability_amount

    return total

def currency_list(owner):
    # filter the database for the queryset
    currencies = Saving.objects.filter(owner=owner).values_list('value_currency', flat=True).distinct()
    return currencies

def past_investment(queryset: QuerySet)-> Money:
    """Getting the total value in USD of past investment transactions"""
    sum_total = Decimal(0)
    for transaction in queryset:
        principal = transaction.investment.principal
        value = transaction.amount
        currency = value.currency
        rate = exchange_rate(currency)[0]
        value = (value.amount - principal.amount)/rate.amount
        sum_total += value
    return Money(sum_total, 'USD')
        
class AggregatedAsset:
    def __init__(self, owner:User, year:int|None=None):
        self.owner = owner
        self.year = year

    def investments(self, investments:QuerySet):
        """A user's investment aggregates within a specified year"""
        # investments = Investment.objects.filter(owner=self.owner).filter(is_active=False)
        if not investments.exists():
            return Money(0, 'USD'), Money(0, 'USD')

        principals, rois = [], []
        for investment in investments:
            if self.year is not None:
                if investment.maturity().year == self.year:
                    principals.append(investment.principal.amount/Decimal(ExchangeRate.objects.get(target_currency=investment.principal.currency).rate))
                    rois.append(investment.roi().amount/Decimal(ExchangeRate.objects.get(target_currency=investment.principal.currency).rate))
            else:
                principals.append(investment.principal.amount/Decimal(ExchangeRate.objects.get(target_currency=investment.principal.currency).rate))
                rois.append(investment.roi().amount/Decimal(ExchangeRate.objects.get(target_currency=investment.principal.currency).rate))
        principal_sum = Money(sum(principals), 'USD')
        rois_sum = Money(sum(rois), 'USD')
        return principal_sum, rois_sum

    def real_estate(self):
        # All rented real estate 
        fixed_asset_sum, earning_sum = 0.0, 0.0
        rented_fixed_assets = FixedAsset.objects.filter(owner=self.owner).exclude(rent=None)
        if rented_fixed_assets.exists():
            if self.year is not None:
                rented_fixed_assets = rented_fixed_assets.filter(rent__date__year=self.year)
        
                if rented_fixed_assets.exists():
                    for estate in rented_fixed_assets:
                        fixed_asset_sum += estate.value.amount/Decimal(ExchangeRate.objects.get(target_currency=estate.value.currency).rate)
                        earning_sum += estate.rent.amount.amount/Decimal(ExchangeRate.objects.get(target_currency=estate.rent.amount.currency).rate)
        return Money(fixed_asset_sum, 'USD'), Money(earning_sum, 'USD')
    

    def business(self):
        # all businesses that are active with FY ending 31st December
        business_sum, earning_sum = 0.0, 0.0

        business = BusinessTransaction.objects.filter(user=self.owner).filter(transaction_type='DR')
        if business.exists():
            if self.year is not None:
                business = business.filter(timestamp__year=self.year)
                
                if business.exists():
                    business_volume = business.annotate(value=F('business__shares')*F('business__unit_cost')).values_list('value', 'amount_currency', 'amount')
                    for biz in business_volume:
                        rate = exchange_rate(biz[1])[0].amount
                        business_sum += biz[0]/rate
                        earning_sum += (biz[2]-biz[0])/rate
        return Money(business_sum, 'USD'), Money(earning_sum, 'USD')
    

    def stock(self):
    # stock transaction
        stock_sum, earning_sum = 0.0, 0.0
        stocks = StockTransaction.objects.filter(user=self.owner).filter(transaction_type='DR')
        if stocks.exists():
            if self.year is not None:
                stocks = stocks.filter(timestamp__year=self.year)
                # if stocks.exists():
                    # stock_volume = stocks.annotate(value=F('stock__units')*F('stock__unit_cost')).values_list('value', 'amount_currency', 'amount')
                stock_volume = stocks.values_list('amount', 'amount_currency')
                if stock_volume.exists():
                    stocks, earnings = list(), list()
                    for stock in stock_volume:
                        rate = exchange_rate(stock[1])[0].amount
                        stocks.append(stock[0]/rate)
                        earnings.append((stock[1]- stock[0])/rate)
                        stock_sum = sum(stocks)
                        earning_sum = sum(earnings)
        return Money(stock_sum, 'USD'), Money(earning_sum, 'USD')

    


