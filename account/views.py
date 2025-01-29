import os
from django.shortcuts import render, redirect
from django.views.generic import CreateView, DetailView, UpdateView, TemplateView
from .forms import SignUpForm, EditProfileForm, PasswordResetForm
from .models import User, Transaction
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from chore.models import FinishedWork
from django.db.models import Sum, Avg
from django.utils.formats import number_format
from django.core.exceptions import ValidationError

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

class ProfileView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = User
    template_name = 'account/profile.html'

    def test_func(self) -> bool | None:
        if self.request.user == self.get_object() or self.request.user.is_staff:
            return True
        return False
    
    def handle_no_permission(self):
        return redirect('forbidden')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        finished_work_all = FinishedWork.objects.filter(worker=self.kwargs['pk'])
        finished_work = finished_work_all.filter(state='done')
        current_points = finished_work.first().worker.points if finished_work.exists() else 0
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
        points_to_ten_dollars = int(float(os.getenv('POINTS_TO_TEN_DOLLARS', '10000')))
        
        options = [(p*points_to_ten_dollars, p*10) for p in range(1, divmod(current_points, points_to_ten_dollars)[0]+1)]
        context['points'] = {'current': current_points, 'to_ten_dollars': points_to_ten_dollars, 'options': options}
        context['transactions'] = Transaction.objects.filter(user__pk=self.kwargs['pk']).order_by('-timestamp')[:7]
        return context
    
    def post(self, request, *args, **kwargs):
        
        redeemable_points = int(''.join(request.POST.get('redeemPoints').split(',')))
        
        try:
            self.get_object().withdraw(redeemable_points, description=request.POST['reason'])
        except ValidationError as ve:
            return render(request, 'account/error.html', {'error_message': ve.message,
                                                          'msg':f'Request to redeem points failed. You have {self.get_object().points} Pts only'})

        return redirect('profile', pk=kwargs['pk'])
    
class EditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'account/edit_profile_form.html'
    form_class = EditProfileForm
    
    def get_success_url(self):
        return reverse_lazy('profile', kwargs={'pk': self.object.pk})  # Redirect to the updated profile

class StatementView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = User
    template_name = 'account/statement.html'

    def test_func(self) -> bool | None:
        if self.request.user == self.get_object() or self.request.user.is_staff:
            return True
        return False
    
    def handle_no_permission(self):
        return redirect('forbidden')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transactions = self.get_object().transactions.all().order_by('-timestamp')
        context['transactions'] = transactions
        # Set up pagination
        paginator = Paginator(transactions, 10)  # 10 items per page
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Add the paginated objects to the context
        context['page_obj'] = page_obj
        return context

class ForbiddenView(TemplateView):
    template_name = 'account/403.html'