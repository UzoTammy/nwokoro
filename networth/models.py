from babel.numbers import format_percent
from decimal import Decimal
from django.shortcuts import redirect
from django.db import models
from django.core.exceptions import ValidationError
from djmoney.models.fields import MoneyField
from djmoney.money import Money
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
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'I: {self.principal} with {self.holder} for {self.duration}'
    
    def maturity(self):
        return self.start_date + timezone.timedelta(days=self.duration)

    def is_matured(self):
        if date.today()>self.maturity():
            return True
        return False
    
    def due_in_days(self):
        return (self.maturity() - date.today()).days
    
    def daily_roi(self):
        return (self.principal * Decimal(self.rate/100) ) / Decimal((365))
    
    def roi(self):
        return self.daily_roi() * Decimal(self.duration)
    
    def present_roi(self):
        if self.due_in_days() <= 0:
            return self.roi()
        return self.daily_roi() * (self.duration - self.due_in_days())
    
    def rollover(self, rate, start_date, duration, option, adjusted_amount, savings_account=None):
        """Rollover
        a. Deactivate current investment
        b. Create a new investment
        c. Create a new transaction
        """

        description1 = 'Principal and interest reinvested'
        description2 = f'Interest from {self}'
            
        amount1 = self.principal
        amount2 =  self.present_roi() + Money(adjusted_amount, amount1.currency)

        self.is_active = False # deactivate investment
        self.save()
            
        if option == 'PI':
            
            Investment.objects.create( # create a new investment
                owner=self.owner,
                holder=self.holder,
                principal=amount1 + amount2,
                rate=rate,
                start_date=start_date,
                duration=duration,
                host_country=self.host_country,
                category=self.category
            )

            InvestmentTransaction.objects.create(
                user=self.owner,
                investment=self,
                amount=amount1 + amount2,
                description=description1,
                timestamp=start_date,
                transaction_type='CR'
            )
        
        else:
            description1 = 'Principal reinvested while the yield is dropped to savings'
            
            Investment.objects.create( # create a new investment
                owner=self.owner,
                holder=self.holder,
                principal=amount1,
                rate=rate,
                start_date=start_date,
                duration=duration,
                host_country=self.host_country,
                category=self.category
            )
            InvestmentTransaction.objects.create(
                user=self.owner,
                investment=self,
                amount=amount1,
                description=description2,
                timestamp=start_date,
                transaction_type='CR'
            )

            # call up savings
            savings_account.value += amount2
            savings_account.save()

            SavingsTransaction.objects.create(
                user=self.owner,
                savings=savings_account,
                amount=amount2,
                description=description2,
                timestamp=start_date,
                transaction_type='CR'
            )
        
    # def terminate(self):
    #     """
    #     Terminate
    #     a. Deactivate current investment
    #     b. Move funds to savings account
    #     c. Create new transaction
    #     """

class Stock(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_stocks")
    holder = models.CharField(max_length=30)
    units = models.PositiveIntegerField()
    unit_cost = MoneyField(max_digits=12, decimal_places=2)
    unit_price = MoneyField(max_digits=12, decimal_places=2)
    host_country = models.CharField(max_length=30)
    date_bought = models.DateTimeField(default=timezone.now)
    date_sold = models.DateTimeField(default=timezone.now, blank=True, null=True)
    stock_type = models.CharField(max_length=30, default='TFSA')


    def __str__(self):
        return f'{self.stock_type} @ {self.holder}'
    
    # def clean(self):
    #     """Ensure cancelled jobs do not get rated"""
    #     super().clean()  # Call parent clean method
    #     if self.date_sold:
    #         if self.date_sold < self.date_bought.date():
    #             raise ValidationError({'date_sold': 'Sold date must be ahead of bought date'})

    def save(self, *args, **kwargs):
        """Call clean before saving."""
        self.clean()
        super().save(*args, **kwargs)

    def is_active(self):
        if self.date_sold:
            return False
        return True
    
    def value(self):
        return self.unit_cost * self.units
    
    def current_worth(self):
        return self.unit_price * self.units
    
    def sell(self, selling_date, adjusted_amount, saving_account, description):
        """
            a. create date_sold
            b. transfer value or less to savings account
            c. generate a transaction
        """

        self.date_sold = selling_date
        self.save()

        """Adjusted amount can be nil or something"""
        amount = self.current_worth() - adjusted_amount

        saving_account.value += amount
        saving_account.save()

        StockTransaction.objects.create(
            user=self.owner,
            stock=self,
            amount=amount,
            description=description,
            timestamp=selling_date,
            transaction_type='CR'
        )

class Saving(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_savings")
    holder = models.CharField(max_length=30)
    value = MoneyField(max_digits=12, decimal_places=2)
    host_country = models.CharField(max_length=30)
    date = models.DateField(default=date.today)
    category = models.CharField(max_length=30, default='TFSA')


    def __str__(self):
        return f'Saving: {self.value}'
    
    def create_investment(self, holder, principal, rate, start_date, duration, category):
    
        investment = Investment.objects.create(
            owner = self.owner,
            holder = holder,
            principal = principal,
            rate = rate,
            start_date = start_date,
            duration = duration,
            host_country = self.host_country,
            category = category
        )

        InvestmentTransaction.objects.create(
            user = self.owner,
            investment = investment,
            amount = principal,
            description = f'Funds from {self.holder} on {start_date}',
            timestamp = start_date,
            transaction_type = 'CR'
        )

        self.value -= principal
        self.save()

        SavingsTransaction.objects.create(
            user = self.owner,
            savings = self,
            amount = principal,
            description = f'Funds to {investment.holder} on {start_date}',
            timestamp = start_date,
            transaction_type = 'DR'
        )
    
    def create_stock(self, holder, units, unit_cost, unit_price, date_bought, stock_type):
        
        stock = Stock.objects.create(
            owner = self.owner,
            holder = holder,
            units = units,
            unit_cost = unit_cost,
            unit_price = unit_price,
            date_bought = date_bought,
            date_sold = None,
            host_country = self.host_country,
            stock_type = stock_type
        )

        StockTransaction.objects.create(
            user = self.owner,
            stock = stock,
            amount = stock.value(),
            description = f'Funds from {self.holder} on {date_bought}',
            timestamp = date_bought,
            transaction_type = 'CR'
        )

        self.value -= stock.value()
        self.save()

        SavingsTransaction.objects.create(
            user = self.owner,
            savings = self,
            amount = stock.value(),
            description = f'Funds to {stock.holder} on {date_bought}',
            timestamp = date_bought,
            transaction_type = 'DR'
        )

    def create_business(self, name, shares, unit_cost, date):
        
        business = Business.objects.create(
            owner = self.owner,
            name = name,
            shares = shares,
            unit_cost = unit_cost,
            date = date,
            host_country = self.host_country,
        )

        BusinessTransaction.objects.create(
            user = self.owner,
            business = business,
            amount = business.capital(),
            description = f'Funds from {self.holder} on {date}',
            timestamp = date,
            transaction_type = 'CR'
        )

        self.value -= business.capital()
        self.save()

        SavingsTransaction.objects.create(
            user = self.owner,
            savings = self,
            amount = business.capital(),
            description = f'Funds to {business.name} on {date}',
            timestamp = date,
            transaction_type = 'DR'
        )

    def create_fixed_asset(self, name, value, date):
        
        fixed_asset = FixedAsset.objects.create(
            owner = self.owner,
            name = name,
            value = value,
            date = date,
            host_country = self.host_country,
        )

        FixedAssetTransaction.objects.create(
            user = self.owner,
            fixed_asset = fixed_asset,
            amount = fixed_asset.value,
            description = f'Funds from {self.holder}',
            timestamp = date,
            transaction_type = 'CR'
        )

        self.value -= fixed_asset.value
        self.save()

        SavingsTransaction.objects.create(
            user = self.owner,
            savings = self,
            amount = fixed_asset.value,
            description = f'Funds to buy {fixed_asset.name}',
            timestamp = date,
            transaction_type = 'DR'
        )

    def borrow_fund(self, source, amount, cost, date):
        # create borrowed fund
        bf = BorrowedFund.objects.create(
            owner = self.owner,
            source = source,
            borrowed_amount = amount,
            settlement_amount = amount + cost,
            settled_amount = Money(0, amount.currency),
            date = date,
            host_country = self.host_country

        )
        # record the transaction
        BorrowedFundTransaction.objects.create(
            user = self.owner,
            borrowed_fund = bf,
            amount = amount,
            description = f'Borrowed funds from {bf.source}',
            timestamp = date,
            transaction_type = 'DR'
        )
        # credit the savings Account
        self.value += amount
        self.save()
        # record the transaction
        SavingsTransaction.objects.create(
            user = self.owner,
            savings = self,
            amount = amount,
            description = f'Borrowed fund from {source}',
            timestamp = date,
            transaction_type = 'CR'
        )

class Business(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    date = models.DateField(default=timezone.now)
    shares = models.PositiveIntegerField()
    unit_cost = MoneyField(max_digits=12, decimal_places=2)
    host_country = models.CharField(max_length=2)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Business'

    def capital(self):
        return self.shares * self.unit_cost
    
class FixedAsset(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    date = models.DateField(default=timezone.now)
    value = MoneyField(max_digits=12, decimal_places=2)
    host_country = models.CharField(max_length=2)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'FixedAsset'
    
class Liability(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    date = models.DateField(default=timezone.now)
    initial_amount = MoneyField(max_digits=12, decimal_places=2)
    balance_amount = MoneyField(max_digits=12, decimal_places=2)
    pay_method = models.CharField(max_length=30)
    interest = models.DecimalField(max_digits=5, decimal_places=2)
    host_country = models.CharField(max_length=2)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Liability'
    
class BusinessTransaction(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_business_transactions")
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='business_transactions')
    amount = MoneyField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    transaction_type = models.CharField(max_length=2) # DR or CR

    def __str__(self):
        return f"{self.user.username}:{self.amount}>>{self.transaction_type}"
    
class FixedAssetTransaction(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_fixed_asset_transactions")
    fixed_asset = models.ForeignKey(FixedAsset, on_delete=models.CASCADE, related_name='fixed_asset_transactions')
    amount = MoneyField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    transaction_type = models.CharField(max_length=2) # DR or CR

    def __str__(self):
        return f"{self.user.username}:{self.amount}>>{self.transaction_type}"

class LiabilityTransaction(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_liability_transactions")
    liability = models.ForeignKey(Liability, on_delete=models.CASCADE, related_name='liability_transactions')
    amount = MoneyField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    transaction_type = models.CharField(max_length=2) # DR or CR

    def __str__(self):
        return f"{self.user.username}:{self.amount}>>{self.transaction_type}"

class InvestmentTransaction(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_investment_transactions")
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE, related_name='investment_transactions')
    amount = MoneyField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    transaction_type = models.CharField(max_length=2) # DR or CR

    def __str__(self):
        return f"{self.user.username}:{self.amount}>>{self.transaction_type}"
    
class StockTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_stock_transactions")
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='stock_transactions')
    amount = MoneyField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    transaction_type = models.CharField(max_length=2) # DR or CR

    def __str__(self):
        return f"{self.user.username}:{self.amount}>>{self.transaction_type}"

class SavingsTransaction(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_savings_transactions")
    savings = models.ForeignKey(Saving, on_delete=models.CASCADE, related_name='savings_transactions')
    amount = MoneyField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    transaction_type = models.CharField(max_length=2) # DR or CR

    def __str__(self):
        return f"{self.user.username}:{self.amount}>>{self.transaction_type}"
 
class BorrowedFund(models.Model):

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.CharField(max_length=50)
    borrowed_amount = MoneyField(max_digits=12, decimal_places=2)
    settlement_amount = MoneyField(max_digits=12, decimal_places=2)
    date = models.DateField()
    repayment_amount = MoneyField(max_digits=12, decimal_places=2, blank=True, null=True)
    repayment_start_date = models.DateField(blank=True, null=True)
    repayment_period = models.CharField(max_length=30, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    settled_amount = MoneyField(max_digits=12, decimal_places=2)
    host_country = models.CharField(max_length=2)

    def __str__(self):
        return f'BorrowedFund from {self.source}'
    
    def expected_number_of_payments(self):
        return int(self.settlement_amount/self.repayment_amount)
    
    def number_of_payments_made(self):
        return self.borrowed_fund_transactions.all()
        
class BorrowedFundTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_borrowed_fund_transactions")
    borrowed_fund = models.ForeignKey(BorrowedFund, on_delete=models.CASCADE, related_name='borrowed_fund_transactions')
    amount = MoneyField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    transaction_type = models.CharField(max_length=2) # DR or CR

    def __str__(self):
        return f"{self.user.username}:{self.amount}>>{self.transaction_type}"

class FinancialData(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    worth = MoneyField(max_digits=12, decimal_places=2)
    savings = MoneyField(max_digits=12, decimal_places=2)
    investment = MoneyField(max_digits=12, decimal_places=2)
    stock = MoneyField(max_digits=12, decimal_places=2)
    business = MoneyField(max_digits=12, decimal_places=2)
    fixed_asset = MoneyField(max_digits=12, decimal_places=2)
    liability = MoneyField(max_digits=12, decimal_places=2)
    roi = MoneyField(max_digits=12, decimal_places=2)
    daily_roi = MoneyField(max_digits=12, decimal_places=2)
    present_roi = MoneyField(max_digits=12, decimal_places=2)
    networth_by_country = models.JSONField(null=True)
    

    def __str__(self):
        return f'{self.date}: {self.worth}'
    
    
    def spread(self):

        return {
            'savings': format_percent(self.savings/self.worth),
            'investment': format_percent(self.investment/self.worth),
            'stock': format_percent(self.stock/self.worth),
            'business': format_percent(self.business/self.worth),
            'fixed_asset': format_percent(self.fixed_asset/self.worth)
        }
    
    def networth(self):
        return self.worth - self.liability


    
