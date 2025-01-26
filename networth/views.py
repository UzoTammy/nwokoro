from decimal import Decimal
from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from django.db.models.aggregates import Sum
from django.views.generic import (TemplateView, CreateView, DetailView, UpdateView, FormView)
from django.contrib.auth.mixins import LoginRequiredMixin
from djmoney.models.fields import Money
from .models import Saving, Investment, ExchangeRate
from .forms import InvestmentCreateForm, SavingForm, InvestmentRolloverForm
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
        investments = Investment.objects.filter(is_active=True)
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


class InvestmentCreateView(LoginRequiredMixin, FormView):
    form_class = InvestmentCreateForm
    template_name = 'networth/investment_form.html'

    def get_success_url(self):
        return reverse_lazy('networth-home')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['pk'] = self.kwargs.get('pk')
        
        return kwargs

    def form_valid(self, form):
        form.cleaned_data['owner'] = self.request.user if self.request.user.is_staff else None
        savings_account = Saving.objects.get(pk=self.kwargs['pk'])        
        savings_account.create_investment(
            holder=form.cleaned_data['holder'],
            principal=form.cleaned_data['principal'],
            rate=form.cleaned_data['rate'],
            start_date=form.cleaned_data['start_date'],
            duration=form.cleaned_data['duration'],
            category=form.cleaned_data['category']
        )
        messages.success(self.request, 'Investment created successfully !!!')

        return super().form_valid(form)

class InvestmentDetailView(LoginRequiredMixin, DetailView):
    model = Investment

class InvestmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Investment
    success_url = reverse_lazy('networth-home')
    form_class = InvestmentCreateForm


class InvestmentRolloverView(LoginRequiredMixin, FormView):
    # model = Investment
    form_class = InvestmentRolloverForm
    success_url = reverse_lazy('networth-home')
    template_name = 'networth/rollover_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        pk = self.kwargs.get('pk')
        kwargs['pk'] = pk
        return kwargs

    def form_valid(self, form):
        form = InvestmentRolloverForm(pk=self.kwargs['pk'])
        inv = Investment.objects.get(pk=self.kwargs['pk'])
        inv.rollover(form.cleaned_data['rate'], form.cleaned_data['start_date'], form.cleaned_data['duration'], 
                     form.cleaned_data['option'], form.cleaned_data['adjusted_amount'], form.cleaned_data['savings_account'])
        return super().form_valid(form)

class SavingCreateView(LoginRequiredMixin, CreateView):
    model = Saving
    form_class = SavingForm
    success_url = reverse_lazy('networth-home')
    
    def form_valid(self, form):
        form.instance.owner = self.request.user if self.request.user.is_staff else None
        return super().form_valid(form)

class SavingDetailView(LoginRequiredMixin, DetailView):
    model = Saving

class SavingUpdateView(LoginRequiredMixin, UpdateView):
    model = Saving
    success_url = reverse_lazy('networth-home')
    form_class = SavingForm

