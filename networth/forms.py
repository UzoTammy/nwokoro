from django import forms
from .models import Investment, Saving

class InvestmentCreateForm(forms.ModelForm):

    holder = forms.CharField(widget=forms.Select(choices=[
        ('Axa Mansard', 'Axa Mansard'), ('Scotia Bank', 'Scotia Bank')
    ]))
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    host_country = forms.CharField(widget=forms.Select(choices=[
        ('NG', 'Nigeria'), ('CA', 'Canada'), ('US', 'USA'), 
    ]))

    class Meta:
        model = Investment
        fields = ['holder', 'principal', 'rate', 'start_date', 'duration', 'host_country']


class SavingForm(forms.ModelForm):

    holder = forms.CharField(widget=forms.Select(choices=[
        ('Axa Mansard', 'Axa Mansard'), ('Scotia Bank', 'Scotia Bank')
    ]))
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    host_country = forms.CharField(widget=forms.Select(choices=[
        ('NG', 'Nigeria'), ('CA', 'Canada'), ('US', 'USA'), 
    ]))

    class Meta:
        model = Saving
        fields = ['holder', 'value', 'date', 'host_country']