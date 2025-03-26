
import requests
import datetime
from celery import shared_task
from .emails import FinancialReport
from networth.models import (ExchangeRate, Investment, Saving, Stock, Business, FixedAsset, BorrowedFund)
from account.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.http import HttpResponse


@shared_task
def fetch_exchange_rate():
    """
    Task to fetch exchange rates and save them to the database.
    """
    api_key = '554c0da083584606b4e7cf01b1994576'  # Replace with your actual API key

    url = 'https://openexchangerates.org/api/latest.json'
    # Specify the currencies to fetch
    target_currencies = ['CAD', 'USD', 'NGN']
    symbols = ','.join(target_currencies)  # Create a comma-separated string: 'CAD,USD,NGN'
    headers = {"accept": "application/json"}

    try:
        response = requests.get(url, params={'app_id': api_key, 'symbols': symbols}, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()
        
        base_currency = data['base']
        rates = data['rates']

        # Save rates in the database
        for target_currency, rate in rates.items():
            ExchangeRate.objects.update_or_create(
                base_currency=base_currency,
                target_currency=target_currency,
                defaults={'rate': rate},
            )
    except requests.exceptions.RequestException as e:
        print(f"Error fetching exchange rates: {e}")

@shared_task
def financial_report_email():
    users = User.objects.filter(is_staff=True).values_list('username', flat=True)
    for user in users:
        savings = Saving.objects.filter(owner__username=user)
        if savings.exists():
            investments = Investment.objects.filter(is_active=True).filter(owner__username=user)
            stocks = Stock.objects.filter(owner__username=user)
            business = Business.objects.filter(owner__username=user)
            fixed_asset = FixedAsset.objects.filter(owner__username=user)
            liability = BorrowedFund.objects.filter(owner__username=user)
            
            fr = FinancialReport(savings, investments, stocks, business, fixed_asset, liability)
            fr.save_report()
            fr.send_email()

def save_financial_data():
    users = User.objects.filter(is_staff=True).values_list('username', flat=True)
    for user in users:
        savings = Saving.objects.filter(owner__username=user)
        if savings.exists():
            investments = Investment.objects.filter(is_active=True).filter(owner__username=user)
            stocks = Stock.objects.filter(owner__username=user)
            business = Business.objects.filter(owner__username=user)
            fixed_asset = FixedAsset.objects.filter(owner__username=user)
            liability = BorrowedFund.objects.filter(owner__username=user)
            
            fr = FinancialReport(savings, investments, stocks, business, fixed_asset, liability)
            fr.save_report()


def send_investment_email(investment: Investment):
    
    from_email = "no-reply@chores.com"

    to_email = [investment.owner.email]

    if investment.due_in_days == 7:
        message = "This is to remind you that your investment will be due one week from today"
    elif investment.due_in_days() == 3:
        message = "Your investment will be due in 3 days. You need to plan next invest if you have not"
    elif investment.due_in_days() == 0:
        message = "Congrats!!! your investment is matured. I hope you have decided your next move."
    else:
        message = None

    html_content = render_to_string('networth/mails/investment_notification.html', {
            'principal': investment.principal,
            'due_date':  datetime.datetime.now() + datetime.timedelta(investment.due_in_days()),
            'yield': investment.roi(),
            'message': message,
            'link_to_investment': f'investment/{investment.pk}/detail/' # http://localhost:8000/networth/investment/5/detail/
        })
    subject = str(investment)

    msg = EmailMultiAlternatives(subject, "plain text", from_email, to_email,
                                     headers={"Reply-To": "nwokorouzo@gmail.com"},)
    
    msg.attach_alternative(html_content, "text/html")
    try:
        msg.send()
    except Exception as e:
        return HttpResponse(f"Failed to send email: {e}")

 
@shared_task
def investment_notification():
    users = User.objects.filter(is_staff=True).values_list('username', flat=True)
    for user in users:
        investments = Investment.objects.filter(owner__username=user)
        for investment in investments:
            if investment.due_in_days() == 7:
                send_investment_email(investment)
            elif investment.due_in_days() == 3:
                send_investment_email(investment)
            elif investment.due_in_days() == 0:
                send_investment_email(investment)
            else:
                pass # do nothing

