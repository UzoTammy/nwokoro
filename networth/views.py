from decimal import Decimal
from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from django.db.models.aggregates import Sum
from django.db.models import F
from django.views.generic import (TemplateView, CreateView, DetailView, UpdateView, FormView)
from django.contrib.auth.mixins import LoginRequiredMixin
from djmoney.models.fields import Money
from .models import Saving, Stock, Investment, ExchangeRate, Business, FinancialData
from .forms import (InvestmentCreateForm, StockCreateForm, StockUpdateForm, SavingForm, 
                    InvestmentRolloverForm, BusinessCreateForm, BusinessUpdateForm, FixedAssetCreateForm)

# from .tasks import financial_report_email


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
        # for financial report summanry
        context['fd'] = FinancialData.objects.latest('date')

        # exchange rate
        canada = ExchangeRate.objects.get(target_currency='CAD')
        nigeria = ExchangeRate.objects.get(target_currency="NGN")
        rate = Money(nigeria.rate/canada.rate, 'NGN')
        context['exchange'] = f'{rate}/CA$ on {canada.updated_at.strftime("%A %d-%b-%Y")}'
        
        # queryset of assets
        investments = Investment.objects.filter(is_active=True).filter(owner=self.request.user)
        stocks = Stock.objects.filter(owner=self.request.user)
        savings = Saving.objects.filter(owner=self.request.user)
        business = Business.objects.filter(owner=self.request.user)

        context['investments'] = investments.order_by('principal_currency')
        context['savings'] = savings.order_by('value_currency')
        context['stocks'] = stocks.order_by('unit_cost_currency')
        context['business'] = business.order_by('unit_cost_currency')

        # Asset total
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

        currencies = stocks.values_list('unit_cost_currency', flat=True).distinct().order_by('unit_cost_currency')
        
        stock_total = list()
        if currencies.exists():
            for currency in currencies:
                stock_total.append(Money(stocks.filter(unit_cost_currency=currency).annotate(value=F('unit_cost') * F('units')).aggregate(Sum('value'))['value__sum'], currency))
        context['stock_total'] = stock_total
        
        business_total = list()
        if currencies.exists():
            for currency in currencies:
                business_total.append(Money(business.filter(unit_cost_currency=currency).annotate(value=F('unit_cost') * F('shares')).aggregate(Sum('value'))['value__sum'], currency))
        context['business_total'] = business_total
        
        # financial_report_email()
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

class StockCreateView(LoginRequiredMixin, FormView):
    form_class = StockCreateForm
    template_name = 'networth/stock_form.html'
    success_url = reverse_lazy('networth-home')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['pk'] = self.kwargs.get('pk')
        return kwargs

    def form_valid(self, form):
        form.cleaned_data['owner'] = self.request.user if self.request.user.is_staff else None
        # form.cleaned_data['date_sold'] = form.cleaned_data['date_bought']

        savings_account = Saving.objects.get(pk=self.kwargs['pk'])        
        savings_account.create_stock(
            holder=form.cleaned_data['holder'],
            units=form.cleaned_data['units'],
            unit_cost=form.cleaned_data['unit_cost'],
            unit_price=form.cleaned_data['unit_cost'],
            date_bought=form.cleaned_data['date_bought'],
            stock_type=form.cleaned_data['stock_type']
        )
        messages.success(self.request, 'Stock investment created successfully !!!')

        return super().form_valid(form)

class StockDetailView(LoginRequiredMixin, DetailView):
    model = Stock

class StockUpdateView(LoginRequiredMixin, UpdateView):
    model = Stock
    success_url = reverse_lazy('networth-home')
    form_class = StockUpdateForm

# Saving
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

# Business
class BusinessCreateView(LoginRequiredMixin, FormView):
    success_url = reverse_lazy('networth-home')
    form_class = BusinessCreateForm
    template_name = 'networth/business_form.html'


    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['pk'] = self.kwargs.get('pk')
        return kwargs


    def form_valid(self, form):
        form.instance.owner = self.request.user

        savings_account = Saving.objects.get(pk=self.kwargs['pk'])        
        savings_account.create_business(
            name=form.cleaned_data['name'],
            shares=form.cleaned_data['shares'],
            unit_cost=form.cleaned_data['unit_cost'],
            date=form.cleaned_data['date'],
        )
        messages.success(self.request, 'Business started successfully !!!')

        return super().form_valid(form)

class BusinessDetailView(LoginRequiredMixin, DetailView):
    model = Business

class BusinessUpdateView(LoginRequiredMixin, UpdateView):
    model = Business
    success_url = reverse_lazy('networth-home')
    form_class = BusinessUpdateForm


class FixedAssetCreateView(LoginRequiredMixin, FormView):
    success_url = reverse_lazy('networth-home')
    form_class = FixedAssetCreateForm
    template_name = 'networth/fixed_asset_form.html'


    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['pk'] = self.kwargs.get('pk')
        return kwargs


    def form_valid(self, form):
        form.instance.owner = self.request.user

        savings_account = Saving.objects.get(pk=self.kwargs['pk'])        
        savings_account.create_fixed_asset(
            name=form.cleaned_data['name'],
            value=form.cleaned_data['value'],
            date=form.cleaned_data['date'],
        )
        messages.success(self.request, 'Business started successfully !!!')

        return super().form_valid(form)
