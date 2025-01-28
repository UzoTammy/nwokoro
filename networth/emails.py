from decimal import Decimal
from django.db.models.aggregates import Sum, Min
from django.db.models import F
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.urls import reverse
from djmoney.models.fields import Money
from .models import ExchangeRate, FinancialData


class FinancialReport:

    def __init__(self, investments, savings, stocks):
        self.investments = investments
        self.savings = savings
        self.stocks = stocks
        
    @staticmethod    
    def convert_to_base(money_list):
        result = list()
        for money in money_list:
            exchange = ExchangeRate.objects.filter(target_currency=money.currency)
            if exchange.exists():
                result.append(Money(money.amount/Decimal(exchange.first().rate), exchange.first().base_currency))
        return sum(result)

    def get_owner(self):
        return self.savings.first().owner

    def get_investment_total(self):
        currencies = self.investments.values_list('principal_currency', flat=True).distinct().order_by('principal_currency')
        investment_total = list()
        if currencies.exists():
            for currency in currencies:
                investment_total.append(Money(self.investments.filter(principal_currency=currency).aggregate(Sum('principal'))['principal__sum'], currency))
        return FinancialReport.convert_to_base(investment_total)
    
    def get_stock_total(self):
        currencies = self.stocks.values_list('unit_cost_currency', flat=True).distinct().order_by('unit_cost_currency')
        stock_total = list()
        if currencies.exists():
            for currency in currencies:
                self.stocks = self.stocks.annotate(value=F('unit_cost') * F('units'))
                stock_total.append(Money(self.stocks.filter(unit_cost_currency=currency).aggregate(Sum('value'))['value__sum'], currency))
        return FinancialReport.convert_to_base(stock_total)
    
    def get_saving_total(self):
        currencies = self.savings.values_list('value_currency', flat=True).distinct().order_by('value_currency')
        savings_total = list()
        if currencies.exists():
            for currency in currencies:
                savings_total.append(Money(self.savings.filter(value_currency=currency).aggregate(Sum('value'))['value__sum'], currency))
        return FinancialReport.convert_to_base(savings_total)
    
    def get_business_total(self):
        return Money(0, 'USD')
    
    def get_fixed_asset_total(self):
        return Money(0, 'USD')
    
    def get_liability_total(self):
        return Money(0, 'USD')

    def getNetworth(self):
        return self.get_investment_total() + self.get_saving_total() + self.get_stock_total() + self.get_business_total() + self.get_fixed_asset_total() - self.get_liability_total()
    
    def get_roi(self):
        return FinancialReport.convert_to_base([x.roi() for x in self.investments])
    
    def get_daily_roi(self):
        return FinancialReport.convert_to_base([x.daily_roi() for x in self.investments])
    
    def get_present_roi(self):
        return FinancialReport.convert_to_base([x.present_roi() for x in self.investments])
    
    
    
    def send_email(self):
        from_email = "no-reply@chores.com"

        subject = "Daily Financial Report"
        to_email = [ self.get_owner().email ]

        html_content = render_to_string('networth/mails/financial_report.html', {
            'networth': self.getNetworth(),
            'investments': self.get_investment_total(),
            'savings': self.get_saving_total(),
            'stocks': self.get_stock_total(),
            'roi': self.get_roi(),
            'daily_roi': self.get_daily_roi(),
            'present_roi': self.get_present_roi(),
            'earliest_due_date': self.investments
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
            present_roi=self.get_present_roi()
        )