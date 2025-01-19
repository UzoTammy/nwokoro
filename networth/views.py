from decimal import Decimal
from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from django.db.models.aggregates import Sum
from django.views.generic import (TemplateView, CreateView, UpdateView)
from django.contrib.auth.mixins import LoginRequiredMixin
from djmoney.models.fields import Money
from .models import Saving, Investment, ExchangeRate
from .forms import InvestmentCreateForm, SavingForm


def convert_to_base(money_list):
    result = list()
    for money in money_list:
        exchange = ExchangeRate.objects.get(target_currency=money.currency)
        result.append(Money(money.amount/Decimal(exchange.rate), exchange.base_currency))
    return sum(result)
    

# Create your views here.
class NetworthHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'networth/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['investments'] = Investment.objects.all().order_by('principal_currency')
        context['savings'] = Saving.objects.all().order_by('value_currency')
        currencies = Investment.objects.values_list('principal_currency', flat=True).distinct().order_by('principal_currency')
        investment_total = list()
        if currencies.exists():
            for currency in currencies:
                investment_total.append(Money(Investment.objects.filter(principal_currency=currency).aggregate(Sum('principal'))['principal__sum'], currency))
        context['investment_total'] = investment_total

        currencies = Saving.objects.values_list('value_currency', flat=True).distinct().order_by('value_currency')
        savings_total = list()
        if currencies.exists():
            for currency in currencies:
                savings_total.append(Money(Saving.objects.filter(value_currency=currency).aggregate(Sum('value'))['value__sum'], currency))
        context['savings_total'] = savings_total
        context['investment_USD'] = convert_to_base(investment_total)
        context['saving_USD'] = convert_to_base(savings_total)
        context['networth'] = sum((convert_to_base(investment_total), convert_to_base(savings_total)))
        return context


class InvestmentCreateView(LoginRequiredMixin, CreateView):
    model = Investment
    success_url = reverse_lazy('networth-home')
    form_class = InvestmentCreateForm

    def form_valid(self, form):
        form.instance.owner = self.request.user if self.request.user.is_staff else None
        return super().form_valid(form)

class InvestmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Investment
    success_url = reverse_lazy('networth-home')
    form_class = InvestmentCreateForm

class SavingCreateView(LoginRequiredMixin, CreateView):
    model = Saving
    success_url = reverse_lazy('networth-home')
    form_class = SavingForm

    def form_valid(self, form):
        form.instance.owner = self.request.user if self.request.user.is_staff else None
        return super().form_valid(form)

class SavingUpdateView(LoginRequiredMixin, UpdateView):
    model = Saving
    success_url = reverse_lazy('networth-home')
    form_class = SavingForm

