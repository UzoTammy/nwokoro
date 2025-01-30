
import requests
from django.utils import timezone
from celery import shared_task
from .emails import FinancialReport
from networth.models import ExchangeRate, Investment, Saving, Stock, Business, FixedAsset, Liability
from account.models import User


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

# @shared_task
def financial_report_email():
    users = User.objects.values_list('username', flat=True)
    for user in users:
        savings = Saving.objects.filter(owner__username=user)
        if savings.exists():
            investments = Investment.objects.filter(is_active=True).filter(owner__username=user)
            stocks = Stock.objects.filter(owner__username=user)
            business = Business.objects.filter(owner__username=user)
            fixed_asset = FixedAsset.objects.filter(owner__username=user)
            liability = Liability.objects.filter(owner__username=user)
            
            fr = FinancialReport(investments, savings, stocks, business, fixed_asset, liability)
            fr.send_email()
            fr.save_report()