from django import forms 


class NumberForm(forms.Form):
    figure = forms.CharField(max_length=25)