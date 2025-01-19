from decimal import Decimal
from django.db import models
from djmoney.models.fields import MoneyField
from account.models import User
from django.utils import timezone
from datetime import date



class ExchangeRate(models.Model):
    base_currency = models.CharField(max_length=3)
    target_currency = models.CharField(max_length=3)
    rate = models.FloatField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.base_currency} to {self.target_currency}: {self.rate}"

# Create your models here.
class Investment(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    holder = models.CharField(max_length=30)
    principal = MoneyField(max_digits=12, decimal_places=2)
    rate = models.FloatField()
    start_date = models.DateField(default=date.today)
    duration = models.PositiveSmallIntegerField()
    host_country = models.CharField(max_length=30)
    category = models.CharField(max_length=30, default='GIC')

    def __str__(self):
        return f'Investment: {self.principal}'
    
    def maturity(self):
        return self.start_date + timezone.timedelta(days=self.duration)

    def is_matured(self):
        if date.today()>self.maturity():
            return True
        return False
    
    def due_in_days(self):
        days = (self.maturity() - date.today()).days
        if self.is_matured():
            return 'Matured'
        return days
    
    def roi_per_day(self):
        return (self.principal * Decimal(self.rate/100) ) / Decimal((365))
    
    def roi(self):
        return self.roi_per_day() * Decimal(self.duration)
    
    def present_roi(self):
        if self.due_in_days() == 'Matured':
            return self.roi()
        return self.roi_per_day() * (self.duration - self.due_in_days())


class Saving(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    holder = models.CharField(max_length=30)
    value = MoneyField(max_digits=12, decimal_places=2)
    host_country = models.CharField(max_length=30)
    date = models.DateField(default=date.today)
    category = models.CharField(max_length=30, default='TFSA')


    def __str__(self):
        return f'Saving: {self.value}'
    