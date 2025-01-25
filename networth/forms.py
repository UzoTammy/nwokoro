from django import forms
from .models import Investment, Saving
from djmoney.forms.fields import MoneyField
from django.core.validators import MaxValueValidator

class OptionChoices:
    HOLDER_OPTION = [
        ('Axa Mansard', 'Axa Mansard'), ('Scotia Bank', 'Scotia Bank'), ('UBA', 'UBA')
    ]
    COUNTRIES = [
        ('NG', 'Nigeria'), ('CA', 'Canada'), ('US', 'USA'), 
    ]
    CATEGORIES = [
        ('GIC', 'GIC'), ('TB', 'Treasury bill'), ('FD', 'Fixed Deposit'), ('CP', 'Commercial Paper'), ('MM','Money Market') 
    ]

class InvestmentCreateForm(forms.ModelForm):
    
    holder = forms.CharField(widget=forms.Select(choices=OptionChoices.HOLDER_OPTION))
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    host_country = forms.CharField(widget=forms.Select(choices=OptionChoices.COUNTRIES))
    category = forms.CharField(widget=forms.Select(choices=OptionChoices.CATEGORIES))

    class Meta:
        model = Investment
        fields = ['holder', 'principal', 'rate', 'start_date', 'duration', 'host_country', 'category']


class SavingForm(forms.ModelForm):

    holder = forms.CharField(widget=forms.Select(choices=OptionChoices.HOLDER_OPTION))
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    host_country = forms.CharField(widget=forms.Select(choices=OptionChoices.COUNTRIES))
    category = forms.CharField(widget=forms.Select(choices=[('TSFA', 'TSFA'), ('Standard', 'Standard')]))

    class Meta:
        model = Saving
        fields = ['holder', 'value', 'date', 'host_country', 'category']


class InvestmentRolloverForm(forms.Form):

    option = forms.ChoiceField(choices=[("PI", "Principal & Interest"), ("PO", "Principal only")], widget=forms.Select(attrs={'id': 'option_select_id'}))
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    rate = forms.FloatField()
    duration = forms.IntegerField(min_value=0, max_value=32767,  # Match the max value of PositiveSmallIntegerField
        validators=[MaxValueValidator(32767)])
    adjusted_amount = forms.DecimalField(max_digits=12, decimal_places=2, initial=0.0, help_text='To normalize the real investment figures')
    savings_account = forms.ModelChoiceField(queryset=Saving.objects.none(), required=False, widget=forms.Select(attrs={'id': 'savings_account_id', 'class': 'form-control'})) #'style': 'display:none'}), required=False)

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        super().__init__(*args, **kwargs)

        if self.pk:
            inv = Investment.objects.get(pk=self.pk)
            queryset = Saving.objects.filter(value_currency=inv.principal.currency)
            self.fields['savings_account'].queryset=queryset
