from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from django.db.models.aggregates import Sum
from django.views.generic import (TemplateView, CreateView, DetailView, ListView, UpdateView)
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Reward
from .forms import AchieveCreateForm

# Create your views here.
class AchieveView(LoginRequiredMixin, TemplateView):
    template_name = 'achieve/home.html'

class AchieveCreateView(LoginRequiredMixin, CreateView):
    model = Reward
    form_class = AchieveCreateForm
    success_url = reverse_lazy('achieve-home')
    template_name = 'achieve/create.html'

    def form_valid(self, form):
        form.instance.issued_by = self.request.user.username
        form.instance.user.deposit(form.instance.point, form.instance.reason)
        # send message
        messages.success(self.request, f"{form.instance.point} points reward credited to {form.instance.user.username}")
        # send mail
        
        return super().form_valid(form)