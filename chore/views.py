from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.utils import timezone
from django.db.models.aggregates import Sum
from django.views.generic import (TemplateView, CreateView, DetailView, ListView, UpdateView)
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Work, AssignWork, JobRegister, FinishedWork, InitiateWork, BonusPoint
from account.models import User, Transaction
from .forms import (AddWorkForm, EarnPointForm, JobRegisterForm, DelegateWorkForm, InitiateWorkForm,
                    InitiateWorkApproveForm, BonusPointForm)
from django.contrib import messages
from .emails import Email


FACTORS = [

    { "note": "requires creativity", "name": "Complexity", "weight": 10 },
    { "note": "deadline needed", "name": "Urgency", "weight": 10 },
    { "note": "critical for satisfaction", "name": "Importance", "weight": 15 },
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

class ChoreDashboard(LoginRequiredMixin, TemplateView):
    template_name = 'chore/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(Email.DATA)
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
        bonus_point_obj = BonusPoint.objects.filter(active=True)
        bonus_point = 0
        if bonus_point_obj.exists():
            for p in bonus_point_obj:
                bonus_point += p.bonus_value * self.get_object().work.point if p.bonus_value <= 1.0 else p.bonus_value
        context['bonus_point'] = bonus_point #int(0.2 * self.get_object().work.point)
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

class WorkDetailView(LoginRequiredMixin, UpdateView):
    model = Work
    form_class = AddWorkForm
    success_url = reverse_lazy('work-list')


class AssignWorkView(LoginRequiredMixin, ListView):
    queryset = AssignWork.objects.filter(state='active')|AssignWork.objects.filter(state='repeat')
    template_name = 'chore/assign_work_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['completed_works'] = AssignWork.objects.filter(state='complete')
        return context
    
    def post(self, request, *args, **kwargs):
        assigned_work = AssignWork.objects.get(pk=request.POST['pk'])
        worker = assigned_work.assigned
        work = assigned_work.work.name
        scheduled_time = assigned_work.schedule
        end_time = assigned_work.end_time
        finished_time = timezone.now()
                  
        if request.POST['supervisorRadios'] == 'done':
            assigned_work.state = 'done'
            rating = float(request.POST['rating'])
            
            # check if bonus point is added to this job
            base_point = assigned_work.work.point
            bonus_point_obj = BonusPoint.objects.filter(active=True)

            if bonus_point_obj.exists():
                bonus_point = 0
                for point in bonus_point_obj:
                    if point.bonus_value <= 1.0:
                        bonus_point += point.bonus_value * base_point
                    else: 
                        bonus_point += point.bonus_value
            else:
                bonus_point=0
            state = 'done'
            reason = ""
            
            # Create the finished work
            fw=FinishedWork.objects.create(
                worker=worker, work=work, base_point=base_point, 
                bonus_point=bonus_point, scheduled_time=scheduled_time,
                end_time=end_time, finished_time=finished_time,
                state=state, rating=rating, reason=reason
            )
            # assigned_work.assigned.points += fw.points()
            assigned_work.assigned.deposit(fw.points(), f'Reward for {fw.work.name} done')
            
        elif request.POST['supervisorRadios'] == 'repeat':
            assigned_work.state = 'repeat'
        else:
            assigned_work.state = 'cancel'
            # create the finished work
            base_point, bonus_point = 0, 0
            state = 'cancel'
            reason = "---" # this will come from a post form indicating is cancellation is due 
                            # expired, not committed or withdrawn
            
            # -- base point:0, bonus point:0, state:cancel, reason: not committed/expired/withdrawn
            FinishedWork.objects.create(
                worker=worker, work=work, base_point=base_point, 
                bonus_point=bonus_point, scheduled_time=scheduled_time,
                end_time=end_time, finished_time=finished_time,
                state=state, rating=0.0, reason=reason
            )
        assigned_work.save()

        return redirect('assign-work-list')

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
        messages.success(self.request, f"Job successfully delegated to {form.instance.assigned}")
        # send mail
        Email.delegate_send_email(self.request, form)
        return super().form_valid(form)

class InitiateWorkCreateView(LoginRequiredMixin, CreateView):
    form_class = InitiateWorkForm
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

    def get_queryset(self):
        if self.request.GET:
            return super().get_queryset().filter(state='cancel')
        return super().get_queryset().filter(state='done')

class ConcludedWorDetailView(LoginRequiredMixin, DetailView):
    model = FinishedWork
    template_name = 'chore/concluded_work_detail.html'
