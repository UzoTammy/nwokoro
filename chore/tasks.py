
import requests
from django.utils import timezone
from celery import shared_task
from .models import AssignWork, FinishedWork
from .emails import Email
from networth.models import ExchangeRate
from django.conf import settings

@shared_task
def delist_expired_job():
    "Remove expired jobs from job list after 3 hours if the job is undone (i.e. in active or repeat atate)"
    assigned_works = AssignWork.objects.filter(state__in=['active', 'repeat'])
    for assigned_work in assigned_works:
        if assigned_work.is_expired():
            assigned_work.state='cancel'
            assigned_work.save()

            FinishedWork.objects.create(
                work=assigned_work.work,
                worker=assigned_work.assigned,
                base_point=0,
                bonus_point=0,
                scheduled_time=assigned_work.schedule,
                end_time=assigned_work.end_time,
                finished_time=timezone.now(),
                state='cancel',
                reason='expired',
                rating=0
            )

@shared_task
def send_me_mail():
    Email.email_dashboard()

@shared_task
def schedule_job():
    """1. go to the job register"""
 


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


# url = "https://openexchangerates.org/api/latest.json?app_id=Required&base=Optional&symbols=Optional&prettyprint=false&show_alternative=false"

# headers = {"accept": "application/json"}

# response = requests.get(url, headers=headers)

# print(response.text)