from django import forms
from .models import Investment, Saving


class OptionChoices:
    HOLDER_OPTION = [
        ('Axa Mansard', 'Axa Mansard'), ('Scotia Bank', 'Scotia Bank')
    ]
    COUNTERIES = [
        ('NG', 'Nigeria'), ('CA', 'Canada'), ('US', 'USA'), 
    ]
    CATEGORIES = [
        ('GIC', 'GIC'), ('TB', 'Treasury bill'), ('FD', 'Fixed Deposit'), ('CP', 'Commercial Paper'), ('MM','Money Market') 
    ]

class InvestmentCreateForm(forms.ModelForm):
    
    holder = forms.CharField(widget=forms.Select(choices=OptionChoices.HOLDER_OPTION))
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    host_country = forms.CharField(widget=forms.Select(choices=OptionChoices.COUNTERIES))
    category = forms.CharField(widget=forms.Select(choices=OptionChoices.CATEGORIES))

    class Meta:
        model = Investment
        fields = ['holder', 'principal', 'rate', 'start_date', 'duration', 'host_country', 'category']


class SavingForm(forms.ModelForm):

    holder = forms.CharField(widget=forms.Select(choices=OptionChoices.HOLDER_OPTION))
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    host_country = forms.CharField(widget=forms.Select(choices=OptionChoices.COUNTERIES))
    category = forms.CharField(widget=forms.Select(choices=[('TSFA', 'TSFA'), ('Standard', 'Standard')]))

    class Meta:
        model = Saving
        fields = ['holder', 'value', 'date', 'host_country', 'category']