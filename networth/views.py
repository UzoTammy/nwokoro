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
from .emails import FinancialReport

def convert_to_base(money_list):
    result = list()
    for money in money_list:
        exchange = ExchangeRate.objects.filter(target_currency=money.currency)
        if exchange.exists():
            result.append(Money(money.amount/Decimal(exchange.first().rate), exchange.first().base_currency))
    return sum(result)
    

# Create your views here.
class NetworthHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'networth/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        investments = Investment.objects.all()
        savings = Saving.objects.all()
        fr = FinancialReport(investments, savings)

        context['investments'] = investments.order_by('principal_currency')
        context['savings'] = savings.order_by('value_currency')
        currencies = investments.values_list('principal_currency', flat=True).distinct().order_by('principal_currency')
        investment_total = list()
        if currencies.exists():
            for currency in currencies:
                investment_total.append(Money(investments.filter(principal_currency=currency).aggregate(Sum('principal'))['principal__sum'], currency))
        context['investment_total'] = investment_total

        currencies = savings.values_list('value_currency', flat=True).distinct().order_by('value_currency')
        savings_total = list()
        if currencies.exists():
            for currency in currencies:
                savings_total.append(Money(savings.filter(value_currency=currency).aggregate(Sum('value'))['value__sum'], currency))
        context['savings_total'] = savings_total
        context['investment_USD'] = fr.get_investment_total #convert_to_base(investment_total)
        context['saving_USD'] =  fr.get_saving_total #convert_to_base(savings_total)
        context['networth'] = fr.getNetworth() #sum((convert_to_base(investment_total), convert_to_base(savings_total)))

        context['roi'] = fr.get_roi()
        context['roi_daily'] = fr.get_daily_roi()
        context['present_roi_total'] = fr.get_present_roi()

        fr.send_email()
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

