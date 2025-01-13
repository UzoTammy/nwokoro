import json
from django import forms
from django.forms import ValidationError
from .models import Work, JobRegister, AssignWork, InitiateWork, BonusPoint
from account.models import User
from django_celery_beat.models import PeriodicTask, IntervalSchedule


class CustomDelegateAssignChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.username  # Replace `name` with the desired field to display


class AddWorkForm(forms.ModelForm):
    kind = forms.CharField(widget=forms.Select(
        choices=[('regular', 'Regular'), ('occasional', 'Occasional'), ('one-time', 'One-time')],
        attrs={'onchange': 'showElements()'}))
    
    user = CustomDelegateAssignChoiceField(
        queryset=User.objects.filter(is_staff=False),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        # initial=User.objects.first() if User.objects.exists() else '-----', 
    )
    duration = forms.IntegerField(required=False, initial=8, label='Duration in hours')

    class Meta:
        model = Work
        fields = ['name', 'point', 'description', 'kind']

class JobRegisterForm(forms.ModelForm):
    assigned_to = CustomDelegateAssignChoiceField(
        queryset=User.objects.filter(is_staff=False),
        widget=forms.Select(attrs={'class': 'form-control'}),
        # initial=User.objects.first() if User.objects.exists() else '-----',
        label="Assigned to",
        help_text='Click to select'
    )

    class Meta:
        model = JobRegister
        fields = ['work', 'duration', 'assigned_to']

class EarnPointForm(forms.ModelForm):
    
    mark = forms.CharField(
        max_length=9, 
        required=True,
        label="",
        widget=forms.TextInput(attrs={'placeholder': 'type the word COMPLETED & submit'})
    )

    def clean_mark(self):
        data = self.cleaned_data['mark'].strip()
        if self.cleaned_data['mark'] != 'COMPLETED':
            raise ValidationError("Enter COMPLETED. Remember your caps lock")
        return data
    
    class Meta:
        model = AssignWork
        fields = []
    
class DelegateWorkForm(forms.ModelForm):
    assigned = CustomDelegateAssignChoiceField(
        queryset=User.objects.filter(is_staff=False),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    
    end_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': "datetime-local", 'class': 'form-control'}))
    class Meta:
        model = AssignWork
        fields = ['work', 'assigned', 'end_time']

class InitiateWorkForm(forms.ModelForm):
    
    class Meta:
        model = InitiateWork
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={
                'placeholder': '''Give details of the job you intend to do.

You can propose points obtainable for this job but note that the details will \
be the primary consideration in deciding the points.''',
                'rows': 5,  # Optional: Control the height of the textarea
                'cols': 40,  # Optional: Control the width of the textarea
            }),
        }

class InitiateWorkApproveForm(forms.ModelForm):
    duration = forms.IntegerField(label='Duration', initial=2)

    def clean(self):
        data = self.cleaned_data
        # print(self.cleaned_data)
        if not self.cleaned_data['point'] > 0:
            raise ValidationError("Point must be a positive integer, if job is to be approved")
        return data

    class Meta:
        model = InitiateWork
        fields = ['duration', 'point']

class BonusPointForm(forms.ModelForm):
    end_time = forms.DateTimeField(label='Date & Time', widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    bonus_value = forms.FloatField(help_text='fraction for percent of base point')

    class Meta:
        model = BonusPoint
        fields = ['title', 'active', 'bonus_value', 'end_time']