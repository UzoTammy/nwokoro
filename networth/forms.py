from django import forms
from django.forms import ValidationError
from .models import Investment, Stock, Saving, Business, FixedAsset
from djmoney.forms.fields import MoneyField
from django.core.validators import MaxValueValidator


class OptionChoices:
    HOLDER_OPTION = [
        ('Axa Mansard', 'Axa Mansard'), ('Scotia Bank',
                                         'Scotia Bank'), ('RBC Bank', 'RBC Bank'),
        ('UBA', 'UBA'), ('FirstBank', 'FirstBank'), ('FCMB',
                                                     'FCMB'), ('FidelityBank', 'FidelityBank'),
        ('Fidson', 'Fidson'), ('Neimeth', 'Neimeth'), ('Transcorp', 'Transcorp'),

    ]
    COUNTRIES = [
        ('NG', 'Nigeria'), ('CA', 'Canada'), ('US', 'USA'),
    ]
    CATEGORIES = [
        ('GIC', 'GIC'), ('TB', 'Treasury bill'), ('FD',
                                                  'Fixed Deposit'), ('CP', 'Commercial Paper'), ('MM', 'Money Market')
    ]
    STOCK_TYPE = [
        ('Scotia Essential', 'Scotia Essential'), ('Scotia Selected',
                                                   'Scotia Selected'), ('Shares', 'Shares')
    ]


class InvestmentCreateForm(forms.ModelForm):

    holder = forms.CharField(widget=forms.Select(
        choices=OptionChoices.HOLDER_OPTION))
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}))
    host_country = forms.CharField(
        widget=forms.Select(choices=OptionChoices.COUNTRIES))
    category = forms.CharField(widget=forms.Select(
        choices=OptionChoices.CATEGORIES))

    class Meta:
        model = Investment
        fields = ['holder', 'principal', 'rate', 'start_date',
                  'duration', 'host_country', 'category']

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        super().__init__(*args, **kwargs)

        if self.pk:
            self.savings_account = Saving.objects.get(pk=self.pk)

    def clean(self):
        if self.savings_account.value.currency != self.cleaned_data['principal'].currency:
            raise ValidationError("Currency cannot mismatch")

        if self.savings_account.value < self.cleaned_data['principal']:
            raise ValidationError("Insufficient fund in saving account")


class StockCreateForm(forms.ModelForm):

    holder = forms.CharField(widget=forms.Select(
        choices=OptionChoices.HOLDER_OPTION))
    date_bought = forms.DateField(
        label='Purchase Date', widget=forms.DateInput(attrs={'type': 'date'}))
    host_country = forms.CharField(
        widget=forms.Select(choices=OptionChoices.COUNTRIES))
    stock_type = forms.CharField(
        widget=forms.Select(choices=OptionChoices.STOCK_TYPE))

    class Meta:
        model = Stock
        fields = ['holder', 'units', 'unit_cost',
                  'date_bought', 'host_country', 'stock_type']

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        super().__init__(*args, **kwargs)

        if self.pk:
            self.savings_account = Saving.objects.get(pk=self.pk)

    def clean(self):
        if self.savings_account.value.currency != self.cleaned_data['unit_cost'].currency:
            raise ValidationError("Currency cannot mismatch")

        if self.savings_account.value < self.cleaned_data['unit_cost'] * self.cleaned_data['units']:
            raise ValidationError("Insufficient fund in saving account")


class StockUpdateForm(forms.ModelForm):

    holder = forms.CharField(widget=forms.Select(
        choices=OptionChoices.HOLDER_OPTION))
    # date_bought = forms.DateField(label='Purchase Date', widget=forms.DateInput(attrs={'type': 'date'}))
    host_country = forms.CharField(
        widget=forms.Select(choices=OptionChoices.COUNTRIES))
    stock_type = forms.CharField(
        widget=forms.Select(choices=OptionChoices.STOCK_TYPE))

    class Meta:
        model = Stock
        fields = ['holder', 'host_country', 'stock_type']


class SavingForm(forms.ModelForm):

    holder = forms.CharField(widget=forms.Select(
        choices=OptionChoices.HOLDER_OPTION))
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    host_country = forms.CharField(
        widget=forms.Select(choices=OptionChoices.COUNTRIES))
    category = forms.CharField(widget=forms.Select(
        choices=[('TSFA', 'TSFA'), ('Standard', 'Standard')]))

    class Meta:
        model = Saving
        fields = ['holder', 'value', 'date', 'host_country', 'category']


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
        widget=forms.Select(choices=OptionChoices.COUNTRIES))

    class Meta:
        model = Business
        fields = ['name', 'date', 'shares', 'unit_cost', 'host_country']

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        super().__init__(*args, **kwargs)

        if self.pk:
            self.savings_account = Saving.objects.get(pk=self.pk)

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
        widget=forms.Select(choices=OptionChoices.COUNTRIES))

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
        widget=forms.Select(choices=OptionChoices.COUNTRIES))

    class Meta:
        model = FixedAsset
        fields = ['name', 'host_country']

    

class BusinessUpdateForm(forms.ModelForm):

    name = forms.CharField(max_length=50)
    # date_bought = forms.DateField(label='Purchase Date', widget=forms.DateInput(attrs={'type': 'date'}))
    host_country = forms.CharField(
        widget=forms.Select(choices=OptionChoices.COUNTRIES))
    
    class Meta:
        model = Stock
        fields = ['name', 'host_country', 'stock_type', 'unit_cost']
