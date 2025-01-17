from django import forms
from .models import Reward
from account.models import User
from chore.forms import CustomDelegateAssignChoiceField

class AchieveCreateForm(forms.ModelForm):

    user = CustomDelegateAssignChoiceField(queryset=User.objects.filter(is_staff=False),
        widget=forms.Select(attrs={'class': 'form-control'}),
        )

    class Meta:
        model = Reward
        fields = ['user', 'reason', 'point']
        widgets = {
            'reason': forms.Textarea(attrs={
                'placeholder': '''Why you are awarding points to this user''',
                'rows': 3,  # Optional: Control the height of the textarea
                'cols': 40,  # Optional: Control the width of the textarea
            }),
        }