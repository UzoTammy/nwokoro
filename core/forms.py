from django import forms 
from crispy_forms.helper import FormHelper


class NumberInputForm(forms.Form):
    enter_number = forms.CharField(max_length=25, label='Enter a number')

    def __init__(self, *args, **kwargs):
        super(NumberInputForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)