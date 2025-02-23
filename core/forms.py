import string
import datetime
from django import forms 
from crispy_forms.helper import FormHelper
from .models import StudentProfile, Config
from account.models import Preference


class NumberInputForm(forms.Form):
    enter_number = forms.CharField(max_length=25, label='Enter a number')

    def __init__(self, *args, **kwargs):
        super(NumberInputForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)

class ProfileForm(forms.Form):
    msg = '(blank is possible)'
    first_name = forms.CharField(max_length=30, label='First Name')
    last_name = forms.CharField(max_length=30, label='Last Name')
    middle_name = forms.CharField(max_length=30, label=f'Middle Name {msg}', required=False)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    email = forms.EmailField(max_length=50)
    gender = forms.ChoiceField(choices=[('Male', 'Male'), ('Female', 'Female')], widget=forms.RadioSelect(
        attrs={'class': 'ml-2'}
    ))
    # adult = forms.BooleanField()

    
    def clean(self):
        dob = self.cleaned_data.pop('date_of_birth')
        email = self.cleaned_data.pop('email') if 'email' in self.cleaned_data else None
        
        for k, v in self.cleaned_data.items():
            if k in ['first_name', 'last_name', 'middle_name', 'gender']:
                self.cleaned_data[k] = v.capitalize()

        for k, field_value in self.cleaned_data.items():
            word = ''
            for letter in field_value:
                if letter in string.ascii_letters:
                    word = word + letter
            self.cleaned_data[k] = word

        self.cleaned_data['middle_name'] = '__NA__' if self.cleaned_data['middle_name'] == '' else self.cleaned_data['middle_name']
        self.cleaned_data.update({'date_of_birth': dob.strftime('%d-%b-%Y')})
        self.cleaned_data.update({'email': email})

        today = datetime.date.today()
        date_eighteen_years_ago = datetime.date(today.year - 18, today.month, today.day)
        status = 'Teen' if dob >= date_eighteen_years_ago else 'Adult'
        self.cleaned_data.update({'age_status': status})

        # take today's month and day and dob's year
        new_date = datetime.date(dob.year, today.month, today.day)
        # compare with dob
        age = today.year - dob.year if new_date >= dob else today.year - dob.year - 1
        self.cleaned_data.update({'age': age})
        if self.cleaned_data['age'] < 13:
            raise forms.ValidationError('Only persons above the age of 12 can own a profile')

    
    def clean_first_name(self):
        first_name = self.cleaned_data['first_name'] 
        if first_name and len(first_name) < 3:
            raise forms.ValidationError('Name must be at least 3 characters long')
        return first_name

class ActivateRegistrationForm(forms.Form):

    activate_registration = forms.BooleanField(required=False)
    
    
class UpdateProfileForm(forms.ModelForm):
    msg = '(blank is possible)'
    middle_name = forms.CharField(max_length=30, label=f'Middle Name {msg}', required=False)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    email = forms.EmailField(max_length=50)
    gender = forms.ChoiceField(choices=[('Male', 'Male'), ('Female', 'Female')], widget=forms.RadioSelect(
        attrs={'class': 'ml-2'}
    ))
    # adult = forms.BooleanField()

    class Meta:
        model = StudentProfile
        fields = ('first_name', 'last_name', 'middle_name', 'date_of_birth', 'email', 'gender')

    def clean(self):
        dob = self.cleaned_data.pop('date_of_birth')
        email = self.cleaned_data.pop('email') if 'email' in self.cleaned_data else None
        
        for k, v in self.cleaned_data.items():
            if k in ['first_name', 'last_name', 'middle_name', 'gender']:
                self.cleaned_data[k] = v.capitalize()

        for k, field_value in self.cleaned_data.items():
            word = ''
            for letter in field_value:
                if letter in string.ascii_letters:
                    word = word + letter
            self.cleaned_data[k] = word

        self.cleaned_data['middle_name'] = '__NA__' if self.cleaned_data['middle_name'] == '' else self.cleaned_data['middle_name']
        self.cleaned_data.update({'date_of_birth': dob})
        self.cleaned_data.update({'email': email})

        today = datetime.date.today()
        date_eighteen_years_ago = datetime.date(today.year - 18, today.month, today.day)
        status = 'Teen' if dob >= date_eighteen_years_ago else 'Adult'
        self.cleaned_data.update({'age_status': status})

        # take today's month and day and dob's year
        new_date = datetime.date(dob.year, today.month, today.day)
        # compare with dob
        age = today.year - dob.year if new_date >= dob else today.year - dob.year - 1
        self.cleaned_data.update({'age': age})
        if self.cleaned_data['age'] < 13:
            raise forms.ValidationError('Only persons above the age of 12 can own a profile')

    
    def clean_first_name(self):
        first_name = self.cleaned_data['first_name'] 
        if first_name and len(first_name) < 3:
            raise forms.ValidationError('Name must be at least 3 characters long')
        return first_name

class MyForm(forms.Form):
    name = forms.CharField(max_length=20)
    email = forms.EmailField(max_length=35)


MyFormSet = forms.formset_factory(MyForm, extra=3)

class PreferenceForm(forms.Form):
    networth = forms.ChoiceField(choices=[('holders', 'Holders'), ('countries', 'Countries')], label='networth')
    action = forms.ChoiceField(choices=[('Add', 'Add'), ('Update', 'Update')])
    new_value = forms.CharField(max_length=20, 
                    help_text='Limited to 20 characters', 
                    widget=forms.TextInput(attrs={'placeholder': 'for add & update only'})
                )
    
