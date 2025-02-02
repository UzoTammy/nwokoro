from decimal import Decimal
from babel.numbers import format_currency
from django.db.models.aggregates import Sum
from django.db.models import F
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.http import HttpResponse
from djmoney.models.fields import Money
from .models import ExchangeRate, FinancialData


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
        return sum(result)

    def get_owner(self):
        return self.savings.first().owner

    def get_countries(self):
        # based on the premise that all host country must have savings account
        save = list(self.savings.values_list(
            'host_country', flat=True).distinct())
        return save

    def get_saving_total(self, country=None):
        savings = self.savings.filter(host_country=country) if country else self.savings

        currencies = savings.values_list(
            'value_currency', flat=True).distinct().order_by('value_currency')
        savings_total = list()
        if currencies.exists():
            for currency in currencies:
                savings_total.append(Money(savings.filter(
                    value_currency=currency).aggregate(Sum('value'))['value__sum'], currency))
        return FinancialReport.convert_to_base(savings_total)

    def get_investment_total(self, country=None):
        investments = self.investments.filter(host_country=country) if country else self.investments

        currencies = investments.values_list(
            'principal_currency', flat=True).distinct().order_by('principal_currency')
        investment_total = list()
        if currencies.exists():
            for currency in currencies:
                investment_total.append(Money(investments.filter(
                    principal_currency=currency).aggregate(Sum('principal'))['principal__sum'], currency))
        return FinancialReport.convert_to_base(investment_total)

    def get_stock_total(self, country=None):
        stocks = self.stocks.filter(host_country=country) if country else self.stocks

        currencies = stocks.values_list(
            'unit_cost_currency', flat=True).distinct().order_by('unit_cost_currency')
        stock_total = list()
        if currencies.exists():
            for currency in currencies:
                stocks = stocks.annotate(
                    value=F('unit_cost') * F('units'))
                stock_total.append(Money(stocks.filter(
                    unit_cost_currency=currency).aggregate(Sum('value'))['value__sum'], currency))
        return FinancialReport.convert_to_base(stock_total)

    def get_business_total(self, country=None):
        business = self.business.filter(host_country=country) if country else self.business

        currencies = business.values_list(
            'unit_cost_currency', flat=True).distinct().order_by('unit_cost_currency')
        total = list()
        if currencies.exists():
            for currency in currencies:
                business = business.annotate(
                    value=F('unit_cost') * F('shares'))
                total.append(Money(business.filter(unit_cost_currency=currency).aggregate(
                    Sum('value'))['value__sum'], currency))
        return FinancialReport.convert_to_base(total)

    def get_fixed_asset_total(self, country=None):
        fixed_asset = self.fixed_asset.filter(host_country=country) if country else self.fixed_asset

        currencies = fixed_asset.values_list(
            'value_currency', flat=True).distinct().order_by('value_currency')
        total = list()
        if currencies.exists():
            for currency in currencies:
                total.append(Money(fixed_asset.filter(
                    value_currency=currency).aggregate(Sum('value'))['value__sum'], currency))
        return FinancialReport.convert_to_base(total)

    def get_liability_total(self, country=None):
        liability = self.liability.filter(host_country=country) if country else self.liability

        currencies = liability.values_list(
            'borrowed_amount_currency', flat=True).distinct().order_by('borrowed_amount_currency')
        total = list()
        if currencies.exists():
            for currency in currencies:
                liability = liability.annotate(
                    balance=F('settlement_amount') - F('settled_amount'))
                total.append(Money(liability.filter(borrowed_amount_currency=currency).aggregate(
                    Sum('balance'))['balance__sum'], currency))

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
        worth = dict()
        countries = self.get_countries()
        for country in countries:
            worth[country] = format_currency(self.getNetworth(country).amount, currency='USD', locale='en_US')
        return worth

    def send_email(self):
        from_email = "no-reply@chores.com"

        subject = "Financial Data Saved to Database"
        to_email = [self.get_owner().email]

        fd = FinancialData.objects.latest('date')

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
            'change_in_networth': self.getNetworth() - fd.networth()
        })

        # Create the email message
        msg = EmailMultiAlternatives(subject, "plain text", from_email, to_email,
                                     headers={"Reply-To": "nwokorouzo@gmail.com"},)
        msg.attach_alternative(html_content, "text/html")

        try:
            msg.send()
            # return HttpResponse("Email sent successfully!")
        except Exception as e:
            return HttpResponse(f"Failed to send email: {e}")

    def save_report(self):
        FinancialData.objects.create(
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
