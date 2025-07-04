import datetime
from decimal import Decimal
from django import forms
from django.forms import ValidationError
from django.utils import timezone
from .models import (Investment, Stock, Saving, Business, FixedAsset, RewardFund, BorrowedFund, InjectFund, Rent)
from account.models import User
from account.models import Preference
from djmoney.forms.fields import MoneyField, Money
from django.core.validators import MaxValueValidator

class OptionChoices:

    @classmethod
    def get_options(cls):
        return {
            'countries': [("CA", 'Canada'), ('NG', 'Nigeria'), ('US', 'United States')],
            'categories': [('GIC', 'GIC'), ('FD', 'Fixed Deposit'), ('TB', 'Treasury Bills'), ('CP', 'Commercial Paper')],
            'stock_type': [('Scotia', 'Scotia')]
        }
    
    PAYMENT_PERIOD = [('monthly', 'Monthly'), ('bi-weekly', 'Bi-weekly'), ('yearly', 'Yearly'), ('daily', 'Daily'), ('one-time', 'One-time')]

class ChoiceOrInputWidget(forms.MultiWidget):
    def __init__(self, choices=(), attrs=None):
        widgets = [
            forms.TextInput(attrs={'placeholder': 'Alternative to name not listed below', 'class': 'form-control'}),
            forms.Select(choices=choices, attrs={'class': 'form-control'}),
        ]
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [None, value]  # Custom input case
        return [None, '']  # Default case

class ComboField(forms.MultiValueField):

    def __init__(self, choices=None, *args, **kwargs):
        self.choices = choices
        widget = ChoiceOrInputWidget(choices=choices)
        fields = [
            forms.ChoiceField(choices=choices, required=False),
            forms.CharField(required=False),
        ]
        super().__init__(fields=fields, require_all_fields=False, widget=widget, *args, **kwargs)
        self.widget = ChoiceOrInputWidget(choices=choices)

    def compress(self, data_list):
        
        if data_list[0] == '':
            return data_list[1]
        return data_list[0] if data_list else None    

class SavingForm(forms.ModelForm):

    holder_select = forms.CharField(widget=forms.Select(choices=()), label='Select Holder', required=False)
    holder_text = forms.CharField(label='Or Type Holder', required=False)
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    host_country = forms.CharField(
        widget=forms.Select(choices=OptionChoices.get_options()['countries'])) #
    category = forms.CharField(widget=forms.Select(
        choices=OptionChoices.get_options()['categories'])) #
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        dynamic_choices = kwargs.pop('choices', [(None, 'List is empty')])  # Get dynamic choices from kwargs
        super().__init__(*args, **kwargs)

        if self.user:
            preference = Preference.objects.get(user=self.user)
            if preference.savings_holders:
                dynamic_choices = [(None, 'List of Holders')] + [(holder, holder) for holder in preference.savings_holders]
            
            self.fields['holder_select'].widget.choices = dynamic_choices
            self.fields['holder_select'].help_text = "If holder is not listed, type the holder below"
    
    class Meta:
        model = Saving
        fields = ['holder_select', 'holder_text', 'value', 'date', 'host_country', 'category']

    def clean(self):
        if self.cleaned_data['holder_select'] == '' and self.cleaned_data['holder_text'] == '':
            raise ValidationError(message='Select Holder or Text Holder must have a value')
        if self.cleaned_data['holder_select'] != '' and self.cleaned_data['holder_text'] != '':
            raise ValidationError(message='Both Select holder and Text holder cannot be filled')    
        
class SavingFormUpdate(forms.ModelForm):
    holder = forms.CharField(widget=forms.Select(choices=()), label='Select Holder', required=False)
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    host_country = forms.CharField(
        widget=forms.Select(choices=OptionChoices.get_options()['countries'])) #
    category = forms.CharField(widget=forms.Select(
        choices=OptionChoices.get_options()['categories'])) #
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        dynamic_choices = kwargs.pop('choices', [(None, 'List is empty')])  # Get dynamic choices from kwargs
        super().__init__(*args, **kwargs)

        if self.user:
            preference = Preference.objects.get(user=self.user)
            if preference.savings_holders:
                dynamic_choices = [(None, 'List of Holders')] + [(holder, holder) for holder in preference.savings_holders]
            
            self.fields['holder'].widget.choices = dynamic_choices
            self.fields['holder'].help_text = "If holder is not listed, type the holder below"
    

    class Meta:
        model = Saving
        fields = ['holder', 'date', 'host_country', 'category']

class ConversionForm(forms.Form):
    CURRENCIES = [('NGN', 'NGN'), ('USD', 'USD'), ('CAD', 'CAD')]

    source_account = forms.ModelChoiceField(queryset=Saving.objects.none(), widget=forms.Select(attrs={'class': 'form-control'}))
    receiver_account = forms.ModelChoiceField(queryset=Saving.objects.none(), widget=forms.Select(attrs={'class': 'form-control'}))
    exchange_rate = MoneyField(decimal_places=2, min_value=1, default_currency='NGN')
    amount = MoneyField(decimal_places=2)

    def __init__(self, *args, **kwargs):
        self.username = kwargs.pop('username', None)
        super().__init__(*args, **kwargs)

        if self.username:
            owner = User.objects.get(username=self.username)
            queryset = Saving.objects.filter(owner=owner)
            self.fields['source_account'].queryset = queryset
            self.fields['receiver_account'].queryset = queryset

              
    def clean(self):
        source_currency = self.cleaned_data["source_account"].value.currency
        receiver_currency = self.cleaned_data["receiver_account"].value.currency

        if self.cleaned_data.get("source_account") == self.cleaned_data.get("receiver_account"):
            raise ValidationError("Conversion is not necessary for same savings account")
        
        if source_currency == receiver_currency:
            raise ValidationError("Source account currency must differ from receiver account currency")
        
        if not (self.cleaned_data['amount'].currency == source_currency or self.cleaned_data['amount'].currency == receiver_currency):
            raise ValidationError(f"Currency must either be {source_currency} or {receiver_currency}")
        
        if not (self.cleaned_data['exchange_rate'].currency == source_currency or self.cleaned_data['exchange_rate'].currency == receiver_currency):
            raise ValidationError(f"Currency must either be {source_currency} or {receiver_currency}")
        
        # normal will be exchange currency matching receicver currency
        exchange_rate = self.cleaned_data['exchange_rate'].amount if self.cleaned_data['exchange_rate'].currency != source_currency else 1/self.cleaned_data['exchange_rate'].amount
        
        if self.cleaned_data['amount'].currency == source_currency:
            converted_amount = Money(round(self.cleaned_data['amount'].amount * exchange_rate, 2), receiver_currency)
        else:
            converted_amount = self.cleaned_data['amount']

            # normalized amount MUST be in same currency with source currency
            self.cleaned_data['amount'] = Money(round(self.cleaned_data['amount'].amount / exchange_rate, 2), source_currency)
        self.cleaned_data['converted_amount'] = converted_amount

        if self.cleaned_data['amount'] > self.cleaned_data['source_account'].value:
            raise ValidationError("Insufficient fund in source account")
        
class InvestmentCreateForm(forms.ModelForm):
    
    holder_select = forms.CharField(label="Select Holder", widget=forms.Select(choices=[(None, 'List is empty')]), required=False) #
    holder_text = forms.CharField(label='Or Enter Holder', required=False, 
                                  widget=forms.TextInput(attrs={'placeholder': 'Required if none is selected above'}))

    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}))
    
    host_country = forms.CharField(
        widget=forms.Select(choices=OptionChoices.get_options().get('countries'))) # OptionChoices.get_options().networth_options['countries']
    
    category = forms.CharField(widget=forms.Select(
        choices=OptionChoices.get_options().get('categories'))) # OptionChoices.get_options().networth_options['categories']

    class Meta:
        model = Investment
        fields = ['holder_select', 'holder_text', 'principal', 'rate', 'start_date',
                  'duration', 'host_country', 'category', 'description']

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.pk:
            self.savings_account = Saving.objects.get(pk=self.pk)

        if self.user:
            preference = Preference.objects.get(user=self.user)

            dynamic_choices = [(None, 'List of Holders')] + [(holder, holder) for holder in preference.investment_holders]
            
            self.fields['holder_select'].widget.choices = dynamic_choices
            self.fields['holder_select'].help_text = "If holder is not listed, fill it below"
    
    def clean(self):
        if self.savings_account.value.currency != self.cleaned_data['principal'].currency:
            raise ValidationError("Currency cannot mismatch")

        if self.savings_account.value < self.cleaned_data['principal']:
            raise ValidationError("Insufficient fund in saving account")
        
class InvestmentUpdateForm(forms.ModelForm):
    
    holder = forms.CharField(widget=forms.Select(choices=[(None, 'List is empty')])) #
    
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}))
    
    host_country = forms.CharField(
        widget=forms.Select(choices=OptionChoices.get_options().get('countries'))) # OptionChoices.get_options().networth_options['countries']
    
    category = forms.CharField(widget=forms.Select(
        choices=OptionChoices.get_options().get('categories'))) # OptionChoices.get_options().networth_options['categories']

    class Meta:
        model = Investment
        fields = ['holder', 'rate', 'start_date',
                  'duration', 'host_country', 'category', 'description']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        
        if self.user:
            preference = Preference.objects.get(user=self.user)
            holders = [(holder, holder) for holder in preference.investment_holders]
            dynamic_choices = [(None, 'List of Holders')] + holders
            self.fields['holder'].widget.choices = dynamic_choices
            
class InvestmentTerminationForm(forms.Form):
    adjusted_amount = forms.DecimalField(
        max_digits=12, decimal_places=2, initial=0.0, help_text='Amount to add or to deduct from accrued interest')
    amount_type = forms.CharField(widget=forms.Select(choices=[('CR', 'CR'), ('DR', 'DR')]))
    savings_account = forms.ModelChoiceField(queryset=Saving.objects.none(), widget=forms.Select(
        attrs={'class': 'form-control'}))  # 'style': 'display:none'}), required=False)
    timestamp = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type':'datetime-local'}), initial=timezone.now())

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        super().__init__(*args, **kwargs)

        if self.pk:
            investment = Investment.objects.get(pk=self.pk)
            queryset = Saving.objects.filter(
                value_currency=investment.principal.currency)
            self.fields['savings_account'].queryset = queryset

class InvestmentRolloverForm(forms.Form):

    option = forms.ChoiceField(choices=[("PI", "Principal & Interest"), (
        "PO", "Principal only")], widget=forms.Select(attrs={'id': 'option_select_id'}))
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}))
    rate = forms.FloatField()
    duration = forms.IntegerField(min_value=0, max_value=32767,  # Match the max value of PositiveSmallIntegerField
                                  validators=[MaxValueValidator(32767)])
    adjusted_amount = forms.DecimalField(
        max_digits=12, decimal_places=2, initial=0.0, help_text='To normalize the real investment figures')
    savings_account = forms.ModelChoiceField(queryset=Saving.objects.none(), required=False, widget=forms.Select(
        attrs={'id': 'savings_account_id', 'class': 'form-control'}))  # 'style': 'display:none'}), required=False)

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        super().__init__(*args, **kwargs)

        if self.pk:
            inv = Investment.objects.get(pk=self.pk)
            queryset = Saving.objects.filter(
                value_currency=inv.principal.currency)
            self.fields['savings_account'].queryset = queryset

class StockCreateForm(forms.ModelForm):
    
    holder_select = forms.CharField(widget=forms.Select(choices=[(None, 'List is empty')]),
                                    label='Select Holder') #
    holder_text = forms.CharField(label='Or Type Holder') #
    
    date_bought = forms.DateField(
        label='Purchase Date', widget=forms.DateInput(attrs={'type': 'date'}))
    host_country = forms.CharField(
        widget=forms.Select(choices=OptionChoices.get_options().get('countries'))) #
    stock_type = forms.CharField(
        widget=forms.Select(choices=OptionChoices.get_options().get('stock_type')))#
    
        
    class Meta:
        model = Stock
        fields = ['holder_select', 'holder_text', 'units', 'unit_cost',
                  'date_bought', 'host_country', 'stock_type']

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.pk:
            self.savings_account = Saving.objects.get(pk=self.pk)

        if self.user:
            preference = Preference.objects.get(user=self.user)
            self.fields['holder_select'].widget.choices = [(holder, holder) for holder in preference.stock_holders]
            self.fields['holder_select'].help_text = "If holder is not listed, you must go to preference to add it"
            

    def clean(self):
        if self.savings_account.value.currency != self.cleaned_data['unit_cost'].currency:
            raise ValidationError("Currency cannot mismatch")

        if self.savings_account.value < self.cleaned_data['unit_cost'] * self.cleaned_data['units']:
            raise ValidationError("Insufficient fund in saving account")

class StockUpdateForm(forms.ModelForm):

    holder = forms.ChoiceField(widget=forms.Select(
        choices=[(None, 'List is empty')])) #
    # date_bought = forms.DateField(label='Purchase Date', widget=forms.DateInput(attrs={'type': 'date'}))
    host_country = forms.CharField(
        widget=forms.Select(choices=OptionChoices.get_options()['countries'])) #
    stock_type = forms.CharField(
        widget=forms.Select(choices=OptionChoices.get_options()['stock_type'])) #
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            preference = Preference.objects.get(user=self.user)
            self.fields['holder'].choices = [(holder, holder) for holder in preference.stock_holders]
            self.fields['holder'].help_text = "If holder is not listed, you must go to preference to add it"
            
    class Meta:
        model = Stock
        fields = ['holder', 'host_country', 'stock_type']

class BusinessCreateForm(forms.ModelForm):
    # holder = forms.ChoiceField(choices=())
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    host_country = forms.CharField(
        widget=forms.Select(choices=OptionChoices.get_options()['countries'])) #

    class Meta:
        model = Business
        fields = ['name', 'date', 'shares', 'unit_cost', 'host_country']

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.pk:
            self.savings_account = Saving.objects.get(pk=self.pk)

        # if self.user:
        #     preference = Preference.objects.get(user=self.user)
        #     names = [(name, name) for name in preference.investment_holders]
        #     self.fields['holder'].choices = names
        #     self.fields['holder'].label = 'Company Name'
        

    def clean(self):
        if self.savings_account.value.currency != self.cleaned_data['unit_cost'].currency:
            raise ValidationError(
                "Currency mismatch: A foreign account cannot be used to establish a business")

        if self.savings_account.value < self.cleaned_data['unit_cost'] * self.cleaned_data['shares']:
            raise ValidationError(
                f"Insufficient fund in saving account. You need {self.cleaned_data['unit_cost'] * self.cleaned_data['shares']}")

class FixedAssetCreateForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    host_country = forms.CharField(
        widget=forms.Select(choices=OptionChoices.get_options()['countries'])) #O

    class Meta:
        model = FixedAsset
        fields = ['name', 'date', 'value', 'host_country']

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        super().__init__(*args, **kwargs)

        if self.pk:
            self.savings_account = Saving.objects.get(pk=self.pk)
        

    def clean(self):
        if self.savings_account.value.currency != self.cleaned_data['value'].currency:
            raise ValidationError(
                "Currency mismatch: A foreign account cannot be used to purchase fixed asset")

        if self.savings_account.value < self.cleaned_data['value']:
            raise ValidationError(
                f"Insufficient fund in saving account. You have {self.savings_account.value} only")

class FixedAssetUpdateForm(forms.ModelForm):
    # date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    host_country = forms.CharField(
        widget=forms.Select(choices=OptionChoices.get_options()['countries'])) #

    class Meta:
        model = FixedAsset
        fields = ['name', 'host_country']

class FixedAssetRentForm(forms.ModelForm):

    # amount = forms.DecimalField(max_digits=12, decimal_places=2)
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=datetime.date.today
    )
    # duration = forms.IntegerField(initial=1)
    period = forms.ChoiceField(choices=[("Y", "Year"), ("M", 'Month')])

    class Meta:
        model = Rent
        fields = ('amount', 'date', 'duration', 'period')

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        super().__init__(*args, **kwargs)

        if self.pk:
            self.fixed_asset = FixedAsset.objects.get(pk=self.pk)

    # def clean(self):
    #     self.cleaned_data['amount'] = Money(self.cleaned_data['amount'], self.fixed_asset.value.currency)
    
class FixedAssetCollectRentForm(forms.Form):
    savings_account = forms.ModelChoiceField(queryset=Saving.objects.none())

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        super().__init__(*args, **kwargs)

        if self.pk:
            fixed_asset = FixedAsset.objects.get(pk=self.pk)
            currency = fixed_asset.value.currency
            self.fields['savings_account'].queryset = Saving.objects.filter(value_currency=currency)
            

class BusinessUpdateForm(forms.ModelForm):

    name = forms.CharField(max_length=50)
    # date_bought = forms.DateField(label='Purchase Date', widget=forms.DateInput(attrs={'type': 'date'}))
    host_country = forms.CharField(
        widget=forms.Select(choices=OptionChoices.get_options()['countries'])) #
    
    class Meta:
        model = Stock
        fields = ['name', 'host_country', 'stock_type', 'unit_cost']

class BusinessPlowBackForm(forms.Form):
    profit = forms.DecimalField(max_digits=12, decimal_places=2)
    plow_back_type = forms.ChoiceField(
        choices=[('P', 'Price'), ('S', 'Share'), ('B', 'Both')])
    price_units = forms.ChoiceField(
        label='Ratio(price:shares)', choices=[('1', '1'), ('1:1', '1:1'), ('1:2', '1:2'),('2:1', '2:1'), ('2:3', '2:3'), ('3:2', '3:2')])
        
    def clean(self):
        if self.cleaned_data['plow_back_type'] == 'B' and self.cleaned_data['price_units'] == '1':
            raise ValidationError('Plow back type and ratio do not match')
        if (self.cleaned_data['plow_back_type'] == 'P' or self.cleaned_data['plow_back_type'] == 'S') and self.cleaned_data['price_units'] != '1':
            raise ValidationError('Plow back type and ratio do not match X')
        
        if self.cleaned_data['price_units'] != '1':
            price_ratio, units_ratio = self.cleaned_data['price_units'].strip().split(':')
            price_ratio, units_ratio = Decimal(price_ratio), Decimal(units_ratio)
            total = price_ratio+units_ratio
            price_amount, units_amount = price_ratio/total * self.cleaned_data['profit'], units_ratio/total * self.cleaned_data['profit']
            self.cleaned_data['price_amount'], self.cleaned_data['units_amount'] = price_amount, units_amount
        else:
            if self.cleaned_data['plow_back_type'] == 'P':
                self.cleaned_data['price_amount'] = self.cleaned_data['profit']
                self.cleaned_data['units_amount'] = Decimal('0.0')
            else:
               self.cleaned_data['price_amount'] =  Decimal('0.0')
               self.cleaned_data['units_amount'] = self.cleaned_data['profit']
        
class BusinessLiquidateForm(forms.Form):
    savings_account = forms.ModelChoiceField(queryset=Saving.objects.none(), label='Drop into')
    timestamp = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        initial=timezone.now
    )
    liquidation_type = forms.ChoiceField(choices=[('P', 'Partial'), ('C', 'Complete')])
    number_of_shares = forms.IntegerField(required=False, widget=forms.NumberInput())
    
    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        super().__init__(*args, **kwargs)

        if self.pk:
            savings = Saving.objects.all()
            self.business = Business.objects.get(pk=self.pk)
            currency = self.business.unit_cost.currency
            qs = savings.filter(value_currency=currency)
            self.fields['savings_account'].queryset = qs
            self.fields['savings_account'].initial = qs.first()
    
    def clean(self):
        if self.cleaned_data['number_of_shares'] is None:
            self.cleaned_data['number_of_shares'] = self.business.shares
        else:
            if self.cleaned_data['number_of_shares'] >= self.business.shares:
                raise ValidationError("All/excess shares can't be taken with partial option")

class BorrowedFundForm(forms.ModelForm):
    savings_account = forms.ModelChoiceField(queryset=Saving.objects.none())
    
    date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
                               initial=timezone.now)
    terminal_date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
                               initial=timezone.now() + timezone.timedelta(days=365),
                               help_text=' default is 1 year from today')
    host_country = forms.CharField(
        widget=forms.Select(choices=OptionChoices.get_options()['countries'])) #
    
    class Meta:
        model = BorrowedFund
        fields = ['date', 'source', 'host_country', 'borrowed_amount', 'settlement_amount', 'terminal_date', 'description']

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        super().__init__(*args, **kwargs)

        if self.pk:
            self.savings_account = Saving.objects.filter(pk=self.pk)
            self.fields['savings_account'].queryset = self.savings_account
            self.fields['savings_account'].initial = self.savings_account.first()
            self.fields['borrowed_amount'].initial = Money(0.00, self.savings_account.first().value.currency)
            self.fields['settlement_amount'].initial = Money(0.00, self.savings_account.first().value.currency)
            self.fields['savings_account'].disabled = True
            

    def clean_borrowed_amount(self):
        if self.cleaned_data['borrowed_amount'].currency != self.savings_account.first().value.currency:
            raise ValidationError('Currency mismatch error')
        return self.cleaned_data['borrowed_amount']
        
    def clean_settlement_amount(self):
        if self.cleaned_data['settlement_amount'].currency != self.savings_account.first().value.currency:
            raise ValidationError('Currency mismatch error')
        if self.cleaned_data['settlement_amount'] < self.cleaned_data['borrowed_amount']:
            raise ValidationError("Borrowed amount cannot be less than settlement amount")
        
        return self.cleaned_data['settlement_amount']  
    
    def clean_terminal_date(self):
        if self.cleaned_data['terminal_date'] < self.cleaned_data['date']:
            raise ValidationError("Settlement date must be a date in the future")
        return self.cleaned_data['terminal_date']
           
class RewardFundForm(forms.ModelForm):
    date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        initial=timezone.now)
    
    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        super().__init__(*args, **kwargs)

        if self.pk:
            self.account = Saving.objects.filter(pk=self.pk)
            self.fields['amount'].initial = Money(0.00, self.account.first().value.currency)
            
    class Meta:
        model = RewardFund
        fields = ['date', 'amount', 'description']

    def clean_amount(self):
        if self.cleaned_data['amount'].currency != self.account.first().value.currency:
            raise ValidationError("Inconsistent currency error")
        if self.cleaned_data['amount'] > self.account.first().value:
            raise ValidationError("Insufficient fund error")
        return self.cleaned_data['amount']
        
class InjectFundForm(forms.ModelForm):
    date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), initial=timezone.now)
    
    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        super().__init__(*args, **kwargs)

        if self.pk:
            self.account = Saving.objects.filter(pk=self.pk)
            self.fields['amount'].initial = Money(0.00, self.account.first().value.currency)
            
    class Meta:
        model = InjectFund
        fields = ['date', 'amount', 'description']

    def clean_amount(self):
        if self.cleaned_data['amount'].currency != self.account.first().value.currency:
            raise ValidationError("Inconsistent currency error")
        return self.cleaned_data['amount']

class LiabilityRepayForm(forms.ModelForm):
    savings_account = forms.ModelChoiceField(queryset=Saving.objects.none(), label='From')
    amount = forms.DecimalField(
        max_digits=12, decimal_places=2, initial=0.0, 
        help_text='Must be less than settlement amount'
    )
    date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
                               initial=timezone.now)
    description = forms.CharField(max_length=250)

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        super().__init__(*args, **kwargs)

        if self.pk:
            self.bf = BorrowedFund.objects.get(pk=self.pk)
            self.fields['settlement_amount'].initial = self.bf.settlement_amount
            self.fields['settlement_amount'].disabled = True
            savings = Saving.objects.filter(value_currency=self.bf.settlement_amount.currency)
            self.fields['savings_account'].queryset = savings
            self.fields['savings_account'].initial = savings.first()
            
            
    class Meta:
        model = BorrowedFund
        fields = ['settlement_amount']

    def clean_amount(self):
        self.cleaned_data['amount'] = Money(self.cleaned_data['amount'], self.cleaned_data['settlement_amount'].currency)
        if self.cleaned_data['amount'] > self.cleaned_data['settlement_amount']:
            raise ValidationError("Excess repayment error") 
        return self.cleaned_data['amount']
    
    def clean(self):
        self.cleaned_data['owner'] = self.bf.owner
    
class SavingsCounterTransferForm(forms.Form):
    receiver_account = forms.ModelChoiceField(queryset=Saving.objects.none(), widget=forms.Select(attrs={'class': 'form-control'}))
    donor_account = forms.ModelChoiceField(queryset=Saving.objects.none(), widget=forms.Select(attrs={'class': 'form-control'}))
    amount = forms.DecimalField(
        max_digits=12, decimal_places=2, initial=0.0, help_text='Must not be greater than donor amount')
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))


    def __init__(self, *args, **kwargs):
        self.username = kwargs.pop('username', None)
        super().__init__(*args, **kwargs)

        if self.username:
            owner = User.objects.get(username=self.username)
            queryset = Saving.objects.filter(owner=owner)
            self.fields['receiver_account'].queryset = queryset
            self.fields['donor_account'].queryset = queryset
        

    def clean(self):
        if self.cleaned_data['receiver_account'] == self.cleaned_data['donor_account']:
            raise ValidationError(message='Both Accounts cannot be the same')
        if self.cleaned_data['receiver_account'].value.currency != self.cleaned_data['donor_account'].value.currency:
            raise ValidationError(message='Receiver and Donor Account currency must be the same')
        if self.cleaned_data['receiver_account'].host_country != self.cleaned_data['donor_account'].host_country:
            raise ValidationError(message='Host country of both accounts must be the same')
        if self.cleaned_data['donor_account'].value.amount < self.cleaned_data['amount']:
            raise ValidationError(message='Insufficient fund in Donor Account')
