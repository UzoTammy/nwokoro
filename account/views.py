from django.shortcuts import render
from django.views.generic import CreateView, DetailView, UpdateView
from .forms import SignUpForm, EditProfileForm, PasswordResetForm
from .models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from chore.models import FinishedWork
from django.db.models import Sum, Avg
from django.utils.formats import number_format

class SignUpView(CreateView):
    model = User
    form_class = SignUpForm
    template_name = 'account/sign_up_form.html'
    success_url = reverse_lazy('login')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Account Details',
                'username',
                'email',
                'date_of_birth',
                'password1',
                'password2',
            ),
            ButtonHolder(
                Submit('register', 'Register', css_class='btn btn-primary')
            )
        )

class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'account/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        finished_work_all = FinishedWork.objects.filter(worker=self.kwargs['pk'])
        finished_work = finished_work_all.filter(state='done')
        if finished_work.exists():
            last_work_done = finished_work.latest('finished_time')
            if last_work_done:
                when_last_work_done = last_work_done.finished_time
                context['last_work'] = when_last_work_done
        context['jobs_completed'] = finished_work.count() if finished_work.exists() else 0
        
        context['base_points'] = finished_work.aggregate(Sum('base_point'))['base_point__sum']
        context['bonus_points'] = finished_work.aggregate(Sum('bonus_point'))['bonus_point__sum']
        if finished_work_all.exists():
            context['effectiveness'] = number_format((finished_work.count() if finished_work.exists() else 0)/finished_work_all.count() * 100, decimal_pos=2) + "%"
            context['rating'] = number_format(finished_work_all.aggregate(Avg('rating'))['rating__avg'] * 10, decimal_pos=0)

        finished_work = FinishedWork.objects.filter(worker=self.kwargs['pk']).filter(state='cancel')
        context['jobs_cancelled'] = finished_work.count() if finished_work.exists() else 0
        return context
    
class EditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'account/edit_profile_form.html'
    form_class = EditProfileForm
    
    def get_success_url(self):
        return reverse_lazy('profile', kwargs={'pk': self.object.pk})  # Redirect to the updated profile
    