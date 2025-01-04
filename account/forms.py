from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordResetForm
from .models import User
from django import forms

class SignUpForm(UserCreationForm):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',  # Native HTML5 date picker
            'class': 'form-control'
        }),
        label="Date of Birth"
    )
    class Meta:
        model = User
        fields = ['username', 'email', 'date_of_birth', 'password1', 'password2']

class EditProfileForm(UserChangeForm):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',  # Native HTML5 date picker
            'class': 'form-control'
        }),
        label="Date of Birth"
    )
    class Meta:
        model = User
        fields = ['username', 'email', 'date_of_birth']


class PasswordResetForm(PasswordResetForm):
    email2 = forms.CharField(max_length=50)

    class Meta:
        fields = ['email', 'email2']