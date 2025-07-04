from babel.numbers import format_percent
from decimal import Decimal
from django.db import models
from djmoney.models.fields import MoneyField
from djmoney.money import Money
from account.models import User
from django.utils import timezone
from datetime import date, datetime, time, timedelta
import calendar

class ExchangeRate(models.Model):
    base_currency = models.CharField(max_length=3)
    target_currency = models.CharField(max_length=3)
    rate = models.FloatField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.base_currency} to {self.target_currency}: {self.rate}"

# Internal Objects - Static.
class Saving(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_savings")
    holder = models.CharField(max_length=50)
    value = MoneyField(max_digits=12, decimal_places=2)
    host_country = models.CharField(max_length=30)
    date = models.DateField(default=date.today)
    category = models.CharField(max_length=30, default='TFSA')
    description = models.CharField(max_length=250, default='')


    def __str__(self):
        return f'Savings: {self.value}'

    def create_investment(self, holder, principal, rate, start_date: datetime, duration, category):
    
        investment = Investment.objects.create(
            owner = self.owner,
            holder = holder,
            principal = principal,
            rate = rate,
            start_date = timezone.make_aware(datetime.combine(start_date, datetime.min.time()), timezone.get_default_timezone()),
            duration = duration,
            host_country = self.host_country,
            category = category
        )

        InvestmentTransaction.objects.create(
            user = self.owner,
            investment = investment,
            amount = principal,
            description = f'Funds from {self.holder} on {start_date}',
            timestamp = timezone.make_aware(datetime.combine(start_date, datetime.min.time()), timezone.get_default_timezone()),
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

    def borrow(self, source, amount, settlement_amount, date, terminal_date, description):
        # create borrowed fund
        bf = BorrowedFund.objects.create(
            owner=self.owner,
            source=source,
            borrowed_amount=amount,
            settlement_amount=settlement_amount,
            date=date,
            savings_account=self,
            terminal_date=terminal_date,
            description=description
        )
        # record the transaction
        BorrowedFundTransaction.objects.create(
            user=self.owner,
            borrowed_fund=bf,
            amount=amount,
            description=f'Borrowed funds from {bf.source}',
            timestamp=date,
            transaction_type='DR'
        )
        # credit the savings Account
        self.value += amount
        self.save()

        # record the transaction
        SavingsTransaction.objects.create(
            user=self.owner,
            savings=self,
            amount=amount,
            description=f'Borrowed fund from {source}',
            timestamp=date,
            transaction_type='CR'
        )

    def fund_transfer(self, donor, amount:Money, date):
        self.value += amount
        self.save()
        donor.value -= amount
        donor.save()

        SavingsTransaction.objects.create(
            user = self.owner,
            savings = self,
            amount = amount,
            description = 'Received from another savings',
            timestamp = datetime.combine(date, time()),
            transaction_type = 'CR'
        )

        SavingsTransaction.objects.create(
            user = self.owner,
            savings = donor,
            amount = amount,
            description = 'Transfered to another savings',
            timestamp = datetime.combine(date, time()),
            transaction_type = 'DR'
        )
    
    def update_holders(self):
        # get all holders in savings
        holders = Saving.objects.filter(owner=self.owner).values_list('holder', flat=True).distinct()
        self.owner.preference.savings_holders = list(holders)
        self.owner.preference.save()

    def convert_fund(self, receiver, amount: Money, converted_amount):
        
        self.value -= amount
        self.save()
        receiver.value += converted_amount
        receiver.save()

        SavingsTransaction.objects.create(
            user = self.owner,
            savings = self,
            amount = amount,
            description = 'Fund conversion',
            timestamp = datetime.now(),
            transaction_type = 'DR'
        )

        SavingsTransaction.objects.create(
            user = self.owner,
            savings = receiver,
            amount = converted_amount,
            description = 'Fund conversion',
            timestamp = datetime.now(),
            transaction_type = 'CR'
        )

# Internal Objects - Instruments
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
    description = models.CharField(max_length=250, default='')


    def __str__(self):
        return f'I: {self.principal}-{self.holder}-{self.duration} days'
    
    def maturity(self)->date:
        return self.start_date + timezone.timedelta(days=self.duration)

    def is_matured(self)->bool:
        if date.today() > self.maturity():
            return True
        return False
    
    def due_in_days(self)->int:
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
        
    def terminate(self, amount, savings, timestamp):
        """
        Terminate
        a. Deactivate current investment
        b. Move funds to savings account
        c. Create new transaction
        """
        self.is_active = False
        self.save()

        InvestmentTransaction.objects.create(
            user=self.owner,
            investment=self,
            amount=amount,
            description="Terminated investment",
            timestamp=timestamp,
            transaction_type='DR'
        )

        savings.value += amount
        savings.save()

        SavingsTransaction.objects.create(
            user=self.owner,
            savings=savings,
            amount=amount,
            description="investment proceed",
            timestamp=timestamp,
            transaction_type='CR'
        )

    def update_holders(self):
        # get all holders in savings
        holders = Investment.objects.filter(owner=self.owner).values_list('holder', flat=True).distinct()
        self.owner.preference.investment_holders = list(holders)
        self.owner.preference.save()

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
    description = models.CharField(max_length=250, default='')


    def __str__(self):
        return f'{self.stock_type} @ {self.holder}'
    
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

    def update_holders(self):
        # get all holders in savings
        holders = Stock.objects.filter(owner=self.owner).values_list('holder', flat=True).distinct()
        self.owner.preference.stock_holders = list(holders)
        self.owner.preference.save()

class Business(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    date = models.DateField(default=timezone.now)
    shares = models.PositiveIntegerField()
    unit_cost = MoneyField(max_digits=12, decimal_places=2)
    host_country = models.CharField(max_length=2)
    description = models.CharField(max_length=250, default='')
    is_active = models.BooleanField(default=True)


    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Business'

    def capital(self)->Money:
        return self.shares * self.unit_cost
    
    def update_holders(self):
        # get all holders in savings
        holders = Business.objects.filter(owner=self.owner).values_list('name', flat=True).distinct()
        self.owner.preference.business_holders = list(holders)
        self.owner.preference.save()

    def plow_back(self, **form_data):
        if form_data['plow_back_type'] == 'B' and form_data['price_units'] == '1':
            raise ValueError('UserInputMismatch error occurred')
        if (form_data['plow_back_type'] == 'P' or form_data['plow_back_type'] == 'S') and form_data['price_units'] != '1':
            raise ValueError('UserInputMismatch error occurred')
        capital = self.capital().amount
        if form_data['price_amount'] == Decimal('0'):
            new_shares = round((capital + form_data['units_amount'])/self.unit_cost.amount, 0)
            self.shares = new_shares
        elif form_data['units_amount'] == Decimal('0'):
            new_price = round((capital + form_data['price_amount'])/self.shares, 2)
            self.unit_cost = new_price
        else:
            new_shares = round((capital + form_data['units_amount'])/self.unit_cost.amount, 0)
            new_price = round((capital + form_data['price_amount'])/new_shares, 2)
            self.shares, self.unit_cost = new_shares, new_price
        self.date = date(year=self.date.year+1, month=self.date.month, day=self.date.day)
        self.save()
        BusinessTransaction.objects.create(
            user=self.owner,
            business=self,
            amount=Money(form_data['profit'], self.unit_cost.currency),
            description=f'Plow back profit for {self.date.year-1} applied',
            timestamp=datetime.combine(self.date, time()),
            transaction_type='CR'
        )

    def liquidate(self, **form_data):
        amount = form_data['number_of_shares'] * self.unit_cost
        
        BusinessTransaction.objects.create(
            user=self.owner,
            business=self,
            amount=amount,
            description=f"Liquidation of {self.name}",
            transaction_type='DR'         
        )

        self.shares -= form_data['number_of_shares']
        if self.shares == 0:
            self.is_active = False
        self.save()

        SavingsTransaction.objects.create(
            user=self.owner,
            savings=form_data['savings_account'],
            amount=amount,
            description='Business liquidation',
            timestamp=form_data['timestamp'],
            transaction_type='CR'
        )
        
class Rent(models.Model):
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    duration = models.IntegerField(default=1)
    period = models.CharField(max_length=5)
    is_active = models.BooleanField(default=True)

    def due_date(self):
        if self.period == 'M':
            
            if self.date.month + self.duration > 12:
                yr, mn = divmod(self.date.month+self.duration, 12)
                year, month = self.date.year+yr, mn
            else:
                year, month = self.date.year, self.date.month + self.duration
        else:
            year, month = self.date.year+self.duration, self.date.month

        return date(year, month, self.date.day)

class FixedAsset(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    date = models.DateField(default=timezone.now)
    value = MoneyField(max_digits=12, decimal_places=2)
    host_country = models.CharField(max_length=2)
    description = models.CharField(max_length=250, default='')
    rent = models.ForeignKey(Rent, on_delete=models.CASCADE, default=None, blank=True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'FixedAsset'
    
    def update_holders(self):
        # get all holders in savings
        holders = FixedAsset.objects.filter(owner=self.owner).values_list('name', flat=True).distinct()
        self.owner.preference.fixed_asset_holders = list(holders)
        self.owner.preference.save()

    def create_rent(self, **form_data):
        rent = Rent.objects.create(**form_data)
        self.rent = rent
        self.save()

    def collect_rent(self, savings_account):
        # rent will move money to saving account
        if self.rent is None:
            raise Exception("Rent is inactive or doesn't exist for this property")
        
        SavingsTransaction.objects.create(
            user=self.owner,
            savings=savings_account,
            amount=self.rent.amount,
            description=f"Rent collected for {self.rent.due_date().strftime('%b %Y')}",
            timestamp=timezone.now()
        )
        savings_account.value.amount += self.rent.amount
        savings_account.save()

        self.rent.date = self.rent.due_date()
        self.rent.save()
        
    def stop_rent(self):
        if self.rent is None:
            raise Exception("Rent do not exist")
        self.rent.is_active = False
        self.rent.save()

    def restore_rent(self):
        if self.rent is None:
            raise Exception("Rent do not exist")
        self.rent.is_active = True
        self.rent.save()
    
        # self.rent = None
        
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

    
# External Objects
class BorrowedFund(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.CharField(max_length=50)
    host_country = models.CharField(max_length=2, default='NG')
    borrowed_amount = MoneyField(max_digits=12, decimal_places=2)
    settlement_amount = MoneyField(max_digits=12, decimal_places=2)
    date = models.DateTimeField()
    savings_account = models.ForeignKey(Saving, on_delete=models.CASCADE)
    description = models.CharField(max_length=250, blank=True)
    terminal_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'Borrow {self.source}: {self.borrowed_amount}'
    
    def repay(self, amount, description, timestamp, savings_account):

        BorrowedFundTransaction.objects.create(
            user=self.owner,
            borrowed_fund=self,
            amount=amount,
            description=description,
            timestamp=timestamp,
            transaction_type='CR'
        ) 
        self.settlement_amount -= amount
        self.save()

        SavingsTransaction.objects.create(
            user=self.owner,
            savings=savings_account,
            amount=amount,
            description=description,
            timestamp=timestamp,
            transaction_type='DR'
        )
        savings_account.value -= amount
        savings_account.save()
  
# There is no need for Rewayd & Inject Trasaction objects
class RewardFund(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(default=timezone.now)
    amount = MoneyField(max_digits=12, decimal_places=2)
    savings_account = models.ForeignKey(Saving, on_delete=models.CASCADE)
    description = models.CharField(max_length=250, blank=True)

    def __str__(self):
        return f"Reward {self.owner.username}: {self.amount}"
    
    def savings_transaction(self):
        
        SavingsTransaction.objects.create(
            user=self.owner,
            savings=self.savings_account,
            amount=self.amount,
            description=self.description,
            timestamp=self.date,
            transaction_type='DR'
        )
        self.savings_account.value -= self.amount
        self.savings_account.save()

class InjectFund(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(default=timezone.now)
    amount = MoneyField(max_digits=12, decimal_places=2)
    savings_account = models.ForeignKey(Saving, on_delete=models.CASCADE)
    description = models.CharField(max_length=250, blank=True)

    def __str__(self):
        return f"Inject {self.owner.username}: {self.amount}"
    
    def savings_transaction(self):
        
        SavingsTransaction.objects.create(
            user=self.owner,
            savings=self.savings_account,
            amount=self.amount,
            description=self.description,
            timestamp=self.date,
            transaction_type='CR'
        )
        self.savings_account.value += self.amount
        self.savings_account.save()
        

# transactions
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
    owner = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
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
    exchange_rate = models.JSONField(null=True)
    

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
    
    def save(self, *args, **kwargs):
        exchanges = ExchangeRate.objects.exclude(target_currency='USD').values_list('target_currency', 'rate')
        result = dict()
        for exchange in exchanges:
            result[exchange[0]] = exchange[1]
        self.exchange_rate = result
        super().save(*args, **kwargs)
        
        

    
