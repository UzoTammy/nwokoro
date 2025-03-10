from django import forms
from django.forms import ValidationError
from django.utils import timezone
from .models import Investment, Stock, Saving, Business, FixedAsset, BorrowedFund
from account.models import User
from account.models import Preference
from core.models import Config
from djmoney.forms.fields import MoneyField, Money
from django.core.validators import MaxValueValidator

class OptionChoices:

    @classmethod
    def get_options(cls):
        return Config.objects.first()
    
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

    def __init__(self, choices=(), *args, **kwargs):
        # self.choices = choices
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
         
class InvestmentCreateForm(forms.ModelForm):
    
    holder = forms.ChoiceField(widget=forms.Select(
        choices=[(None, 'List is empty')])) #
    
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}))
    
    host_country = forms.CharField(
        widget=forms.Select(choices=OptionChoices.get_options().networth_options['countries'])) # OptionChoices.get_options().networth_options['countries']
    
    category = forms.CharField(widget=forms.Select(
        choices=OptionChoices.get_options().networth_options['categories'])) # OptionChoices.get_options().networth_options['categories']

    class Meta:
        model = Investment
        fields = ['holder', 'principal', 'rate', 'start_date',
                  'duration', 'host_country', 'category']

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.pk:
            self.savings_account = Saving.objects.get(pk=self.pk)

        if self.user:
            preference = Preference.objects.get(user=self.user)
            if 'holders' in preference.networth:
                dynamic_choices = [(None, 'List of Holders')]
                dynamic_choices = dynamic_choices + [(holder, holder) for holder in preference.networth['holders']]#
            self.fields['holder'].choices = dynamic_choices
            self.fields['holder'].help_text = "If holder is not listed, you must go to preference to add it"
    
    def clean(self):
        if self.savings_account.value.currency != self.cleaned_data['principal'].currency:
            raise ValidationError("Currency cannot mismatch")

        if self.savings_account.value < self.cleaned_data['principal']:
            raise ValidationError("Insufficient fund in saving account")
        
class StockCreateForm(forms.ModelForm):
    
    holder = forms.ChoiceField(widget=forms.Select(
        choices=[(None, 'List is empty')])) #
    
    date_bought = forms.DateField(
        label='Purchase Date', widget=forms.DateInput(attrs={'type': 'date'}))
    host_country = forms.CharField(
        widget=forms.Select(choices=OptionChoices.get_options().networth_options['countries'])) #
    stock_type = forms.CharField(
        widget=forms.Select(choices=OptionChoices.get_options().networth_options['stock_type']))#
    
        
    class Meta:
        model = Stock
        fields = ['holder', 'units', 'unit_cost',
                  'date_bought', 'host_country', 'stock_type']

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.pk:
            self.savings_account = Saving.objects.get(pk=self.pk)

        if self.user:
            preference = Preference.objects.get(user=self.user)
            if 'holders' in preference.networth:
                self.fields['holder'].choices = [(holder, holder) for holder in preference.networth['holders']]
                self.fields['holder'].help_text = "If holder is not listed, you must go to preference to add it"
            

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
        widget=forms.Select(choices=OptionChoices.get_options().networth_options['countries'])) #
    stock_type = forms.CharField(
        widget=forms.Select(choices=OptionChoices.get_options().networth_options['stock_type'])) #
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            preference = Preference.objects.get(user=self.user)
            if 'holders' in preference.networth:
                self.fields['holder'].choices = [(holder, holder) for holder in preference.networth['holders']]
                self.fields['holder'].help_text = "If holder is not listed, you must go to preference to add it"
            
    class Meta:
        model = Stock
        fields = ['holder', 'host_country', 'stock_type']

class SavingForm(forms.ModelForm):

    holder = forms.ChoiceField(widget=forms.Select(
        choices=())) #
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    host_country = forms.CharField(
        widget=forms.Select(choices=OptionChoices.get_options().networth_options['countries'])) #
    category = forms.CharField(widget=forms.Select(
        choices=OptionChoices.get_options().networth_options['categories'])) #
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        dynamic_choices = kwargs.pop('choices', [(None, 'List is empty')])  # Get dynamic choices from kwargs
        super().__init__(*args, **kwargs)

        if self.user:
            preference = Preference.objects.get(user=self.user)
            if 'holders' in preference.networth:
                dynamic_choices = [(None, 'List of Holders')]
                dynamic_choices = dynamic_choices + [(holder, holder) for holder in preference.networth['holders']]#
            self.fields['holder'].choices = dynamic_choices
            self.fields['holder'].help_text = "If holder is not listed, you must go to preference to add it"
    
    class Meta:
        model = Saving
        fields = ['holder', 'value', 'date', 'host_country', 'category']

class SavingFormUpdate(SavingForm):

    class Meta:
        model = Saving
        fields = ['holder', 'date', 'host_country', 'category']

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

class BusinessCreateForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    host_country = forms.CharField(
        widget=forms.Select(choices=OptionChoices.get_options().networth_options['countries'])) #

    class Meta:
        model = Business
        fields = ['name', 'date', 'shares', 'unit_cost', 'host_country']

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.pk:
            self.savings_account = Saving.objects.get(pk=self.pk)

        if self.user:
            preference = Preference.objects.get(user=self.user)
            if 'holders' in preference.networth:
                dynamic_choices = [(holder, holder) for holder in preference.networth['holders']]
            self.fields['name'] = ComboField(choices=dynamic_choices)
            self.fields['name'].label = 'Company Name'
        

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
        widget=forms.Select(choices=OptionChoices.get_options().networth_options['countries'])) #O

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
        widget=forms.Select(choices=OptionChoices.get_options().networth_options['countries'])) #

    class Meta:
        model = FixedAsset
        fields = ['name', 'host_country']

class BusinessUpdateForm(forms.ModelForm):

    name = forms.CharField(max_length=50)
    # date_bought = forms.DateField(label='Purchase Date', widget=forms.DateInput(attrs={'type': 'date'}))
    host_country = forms.CharField(
        widget=forms.Select(choices=OptionChoices.get_options().networth_options['countries'])) #
    
    class Meta:
        model = Stock
        fields = ['name', 'host_country', 'stock_type', 'unit_cost']

class BorrowedFundForm(forms.ModelForm):
    cost_of_fund = MoneyField(max_digits=12, decimal_places=2)
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    savings_account = forms.ModelChoiceField(queryset=Saving.objects.none())
    host_country = forms.CharField(
        widget=forms.Select(choices=OptionChoices.get_options().networth_options['countries'])) #


    class Meta:
        model = BorrowedFund
        fields = ['date', 'source', 'borrowed_amount', 'host_country']

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        super().__init__(*args, **kwargs)

        if self.pk:
            self.savings_account = Saving.objects.filter(pk=self.pk)
            self.fields['savings_account'].queryset = self.savings_account
            self.fields['savings_account'].initial = self.savings_account.first()
            self.fields['savings_account'].disabled = True
            self.fields['borrowed_amount'].initial = Money(0.00, self.savings_account.first().value.currency)
            self.fields['cost_of_fund'].initial = Money(0.00, self.savings_account.first().value.currency)
            self.fields['host_country'].initial = self.savings_account.first().host_country

    def clean_borrowed_amount(self):
        if self.cleaned_data['borrowed_amount'].currency != self.savings_account.first().value.currency:
            raise ValidationError('Currency mismatch: Check your currency selection')
        return self.cleaned_data['borrowed_amount']
        
    def clean_settlement_amount(self):
        if self.cleaned_data['settlement_amount'].currency != self.savings_account.first().value.currency:
            raise ValidationError('Currency mismatch: Check your currency selection')
        return self.cleaned_data['settlement_amount']
        
class InvestmentTerminationForm(forms.Form):
    adjusted_amount = forms.DecimalField(
        max_digits=12, decimal_places=2, initial=0.0, help_text='To normalize the real investment figures')
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
    