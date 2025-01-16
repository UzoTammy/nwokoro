from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.utils import timezone
from django.db.models.aggregates import Sum
from django.views.generic import (TemplateView, CreateView, DetailView, ListView, UpdateView)
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.
class AchieveView(LoginRequiredMixin, TemplateView):
    template_name = 'achieve/home.html'