from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.utils import timezone
from django.db.models.aggregates import Sum
from django.views.generic import (TemplateView, CreateView, DetailView, ListView, UpdateView, FormView)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Work, AssignWork, JobRegister, FinishedWork, InitiateWork, BonusPoint
from core.models import Config
from account.models import User, Transaction
from .forms import (AddWorkForm, EarnPointForm, JobRegisterForm, DelegateWorkForm, InitiateWorkForm,
                    InitiateWorkApproveForm, BonusPointForm, MyModelForm, CompletedJobDecisionForm)
from django.contrib import messages
from .emails import Email


FACTORS = [

    {"note": "requires creativity", "name": "Complexity", "weight": 10 },
    {"note": "deadline needed", "name": "Urgency", "weight": 10 },
    {"note": "critical for satisfaction", "name": "Importance", "weight": 15 },
    {"note": "will take several hours", "name": "Time Required", "weight": 10 },
    {"note": "requires specific tools and data", "name": "Resources Needed", "weight": 5 },
    {"note": "relies on inputs from one other person", "name": "Dependencies", "weight": 5 },
    {"note": "failure could harm client relationship", "name": "Risk", "weight": 15 },
    {"note": "directly contributes to business goals", "name": "Alignment with Goals", "weight": 15 },
    {"note": "requires significant focus and energy", "name": "Effort", "weight": 10 },
    {"note": "other tasks must be delayed", "name": "Opportunity Cost", "weight": 5 }
]

# Create your views here.
class ChoreHome(TemplateView):
    template_name = 'chore/home.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['works'] = Work.objects.all()
        context['initiatedjobs'] = InitiateWork.objects.filter(approved=False)
        return context
    
class RegistrationMessage(TemplateView):
    template_name = 'chore/registration_message.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activate_registration'] = Config.objects.first().activate_registration
        return context


class ChoreDashboard(LoginRequiredMixin, TemplateView):
    template_name = 'chore/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        workers = User.objects.filter(is_staff=False)
        finished_works = FinishedWork.objects.all()
        transactions = Transaction.objects.all()

        context.update(Email.get_context(workers, finished_works, transactions))
        return context

class ChoreSetupView(LoginRequiredMixin, TemplateView):
    template_name = 'chore/setup.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bonus_list'] = BonusPoint.objects.all()
        return context

class WorkCreateView(LoginRequiredMixin, CreateView):
    model = Work
    form_class = AddWorkForm
    success_url = reverse_lazy('work-list')

    def form_valid(self, form):
        if form.cleaned_data['kind'] == 'regular':
            response = super().form_valid(form)
            JobRegister.objects.create(
                work=form.instance,
                assigned_to=form.cleaned_data['user'],
                duration=form.cleaned_data['duration'])
            return response
        return super().form_valid(form)

class WorkEvaluateView(LoginRequiredMixin, TemplateView):
    template_name = 'chore/work_evaluate_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['factors'] = FACTORS
        return context

class BonusPointCreateView(LoginRequiredMixin, CreateView):
    model = BonusPoint
    success_url = reverse_lazy('chore-setup')
    form_class = BonusPointForm
    template_name = 'chore/bonus_form.html'
    
class BonusUpdateView(LoginRequiredMixin, UpdateView):
    model = BonusPoint
    template_name = 'chore/bonus_form.html'
    form_class = BonusPointForm
    success_url = reverse_lazy('chore-setup')

class WorkDoneView(LoginRequiredMixin, UpdateView):
    template_name = 'chore/work_done_form.html'
    model = AssignWork
    form_class = EarnPointForm
    success_url = reverse_lazy('chore-home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['expired'] = True if self.get_object().end_time <= timezone.now() else False
        completed_job = AssignWork.objects.get(pk=self.kwargs['pk'])
        bonus = BonusPoint.objects.filter(active=True)
        bonus_point = 0
        if bonus.exists():
            for obj in bonus:
                if obj.bonus_value <= 1:
                    bonus_point += obj.bonus_value * completed_job.work.point
                else:
                    bonus_point += obj.bonus_value
        context['bonus_point'] = bonus_point
        
        return context

        
    def form_valid(self, form):
        if form.instance.assigned != self.request.user and not self.request.user.is_staff: 
            messages.warning(self.request, 'This Job did not submit because you are not the owner.')
            return redirect('work-done', pk=self.kwargs['pk'])
        
        form.instance.state = 'complete'
        form.instance.save()
        messages.success(self.request, 'Successfully submitted, If job is done properly you will earn points')
        return super().form_valid(form)

class WorkListView(LoginRequiredMixin, ListView):
    model = Work
    ordering = 'name'
    paginate_by = 10

class WorkDetailView(LoginRequiredMixin, UpdateView):
    model = Work
    form_class = AddWorkForm
    success_url = reverse_lazy('work-list')


class DelegateWorkCreateView(LoginRequiredMixin, CreateView):
    form_class = DelegateWorkForm
    model = AssignWork
    success_url = reverse_lazy('assign-work-list')
    template_name = 'chore/delegate_initiate_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assignment'] = 'Delegate'
        return context
    
    def form_valid(self, form):
        form.instance.state = 'active'
        form.save()
        messages.success(self.request, f"Job successfully delegated to {form.instance.assigned.username}")
        # send mail
        Email.delegate_send_email(self.request, form)
        return super().form_valid(form)

# CompleteWorkView - where complete is marked
class AssignWorkView(LoginRequiredMixin, ListView):
    queryset = AssignWork.objects.filter(state='active')|AssignWork.objects.filter(state='repeat')
    template_name = 'chore/assign_work_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['completed_works'] = AssignWork.objects.filter(state='complete')
        return context
    
class CompletedJobDecisionView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'chore/completed_job_decision.html'
    success_url = reverse_lazy('assign-work-list')
    form_class = CompletedJobDecisionForm # this form was not built

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        completed_job = AssignWork.objects.get(pk=self.kwargs['num'])
        context['object'] = completed_job

        bonus = BonusPoint.objects.filter(active=True)
        bonus_point = 0
        if bonus.exists():
            for obj in bonus:
                if obj.bonus_value <= 1:
                    bonus_point += obj.bonus_value * completed_job.work.point
                else:
                    bonus_point += obj.bonus_value
        context['bonus_point'] = bonus_point
        context['bonus'] = bonus
        return context
    
    def test_func(self):
        if self.request.user.is_staff:
            return True
        return False
    
    
    def form_valid(self, form, **kwargs):
        data = self.get_context_data(**kwargs)
        completed_job = data['object']

        if self.request.POST['decision'] == 'done':
            completed_job.state = 'done'
            completed_job.save()

            # Create the finished work
            fw=FinishedWork.objects.create(
                worker=completed_job.assigned, work=completed_job.work, base_point=completed_job.work.point, 
                bonus_point=data['bonus_point'], scheduled_time=completed_job.schedule,
                end_time=completed_job.end_time, finished_time=timezone.now(),
                state=completed_job.state, rating=float(self.request.POST['rating']), reason=''
            )
            # assigned_work.assigned.points += fw.points()
            completed_job.assigned.deposit(fw.points(), f'Reward for {fw.work.name} done')

        elif self.request.POST['decision'] == 'cancel':
            completed_job.state = 'cancel'
            completed_job.save()

            FinishedWork.objects.create(
                worker=completed_job.assigned, work=completed_job.work, base_point=0, 
                bonus_point=0, scheduled_time=completed_job.schedule,
                end_time=completed_job.end_time, finished_time=timezone.now(),
                state=completed_job.state, rating=0.0, reason=self.request.POST['reason']
            )
        else:
            completed_job.state = 'repeat'
            completed_job.save()

        return super().form_valid(form, **kwargs)


class JobRegisterListView(LoginRequiredMixin, ListView):
    model = JobRegister
    template_name = 'chore/work_register_list.html'

class JobRegisterCreateView(LoginRequiredMixin, CreateView):
    model = JobRegister
    template_name = 'chore/work_register_form.html'
    form_class = JobRegisterForm  
    success_url = reverse_lazy('job-register-list')

class JobRegisterUpdateView(LoginRequiredMixin, UpdateView):
    model = JobRegister
    template_name = 'chore/work_register_form.html'
    form_class = JobRegisterForm  
    success_url = reverse_lazy('job-register-list')


class InitiateWorkCreateView(LoginRequiredMixin, CreateView):
    form_class = MyModelForm
    model = InitiateWork
    # fields = ['name', 'description']
    success_url = reverse_lazy('chore-home')
    template_name = 'chore/initiate_work_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assignment'] = 'Initiate'
        return context
    
    def form_valid(self, form):
        form.instance.worker = self.request.user
        form.save()
        messages.success(self.request, f"You have initiated {form.instance.name} job successfully !!!")
        # send mail
        Email.initiate_send_email(self.request, form)
        return super().form_valid(form)
    
class InitiateWorkDetailView(LoginRequiredMixin, DetailView):
    model = InitiateWork
    template_name = 'chore/initiate_work_detail.html'

class InitiateWorkApproveView(LoginRequiredMixin, UpdateView):
    model = InitiateWork
    template_name = 'chore/initiate_work_approve_form.html'
    form_class = InitiateWorkApproveForm
    success_url = reverse_lazy('chore-home')
    
    def form_valid(self, form):
        form.instance.approved = True
        form.save()

        # Create work
        obj = self.get_object()
        
        work = Work.objects.create(
            name=obj.name,
            point=obj.point,
            description=obj.description
        )
        
        assigned_work = AssignWork.objects.create(
            work=work,
            assigned=obj.worker,
            source='initiated'
        )
        
        assigned_work.end_time = assigned_work.schedule + timezone.timedelta(hours=form.cleaned_data['duration'])
        assigned_work.save()
        
        # send email
        Email.approve_send_email(self.request, form)
        return super().form_valid(form)

class ConcludedWorkListView(LoginRequiredMixin, ListView):
    model = FinishedWork
    template_name = 'chore/concluded_work.html'
    paginate_by = 10
    ordering = '-scheduled_time'

class ConcludedWorDetailView(LoginRequiredMixin, DetailView):
    model = FinishedWork
    template_name = 'chore/concluded_work_detail.html'

