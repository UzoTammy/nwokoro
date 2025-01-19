from decimal import Decimal
from django.db.models.aggregates import Sum
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.urls import reverse
from djmoney.models.fields import Money
from .models import ExchangeRate


class FinancialReport:

    def __init__(self, investments, savings):
        self.investments = investments
        self.savings = savings
        
    @staticmethod    
    def convert_to_base(money_list):
        result = list()
        for money in money_list:
            exchange = ExchangeRate.objects.filter(target_currency=money.currency)
            if exchange.exists():
                result.append(Money(money.amount/Decimal(exchange.first().rate), exchange.first().base_currency))
        return sum(result)

    def get_investment_total(self):
        currencies = self.investments.values_list('principal_currency', flat=True).distinct().order_by('principal_currency')
        investment_total = list()
        if currencies.exists():
            for currency in currencies:
                investment_total.append(Money(self.investments.filter(principal_currency=currency).aggregate(Sum('principal'))['principal__sum'], currency))
        return FinancialReport.convert_to_base(investment_total)
    
    def get_saving_total(self):
        currencies = self.savings.values_list('value_currency', flat=True).distinct().order_by('value_currency')
        savings_total = list()
        if currencies.exists():
            for currency in currencies:
                savings_total.append(Money(self.savings.filter(value_currency=currency).aggregate(Sum('value'))['value__sum'], currency))
        return FinancialReport.convert_to_base(savings_total)
    
    def getNetworth(self):
        return self.get_investment_total() + self.get_saving_total()
    
    def get_roi(self):
        return FinancialReport.convert_to_base([x.roi() for x in self.investments])
    
    def get_daily_roi(self):
        return FinancialReport.convert_to_base([x.daily_roi() for x in self.investments])
    
    def get_present_roi(self):
        return FinancialReport.convert_to_base([x.present_roi() for x in self.investments])
    
    def send_email(self):
        from_email = "no-reply@chores.com"

        subject = "Daily Finacial Report"
        to_email = [ 'uzo.tammy@gmail.com' ]

        html_content = render_to_string('networth/mails/financial_report.html', {
            'networth': self.getNetworth(),
            'investments': self.get_investment_total(),
            'savings': self.get_saving_total(),
            'roi': self.get_roi(),
            'daily_roi': self.get_daily_roi(),
            'present_roi': self.get_present_roi(),
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