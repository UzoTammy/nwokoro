import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models.aggregates import Sum, Min, Max
from django.db.models import F
from django.views.generic import (TemplateView, ListView,  CreateView, DetailView, UpdateView, FormView)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from djmoney.models.fields import Money
from .models import Saving, Stock, Investment, ExchangeRate, Business, FinancialData, FixedAsset, BorrowedFund
from .forms import (InvestmentCreateForm, InvestmentUpdateForm, StockCreateForm, StockUpdateForm, SavingForm, SavingFormUpdate,
                    InvestmentRolloverForm, InvestmentTerminationForm, BusinessCreateForm, BusinessUpdateForm, 
                    FixedAssetCreateForm, FixedAssetUpdateForm, SavingsCounterTransferForm,
                    BorrowedFundForm)
from .plots import bar_chart, donut_chart
from babel.numbers import format_percent
from networth.models import ExchangeRate

    

# Create your views here.
class NetworthHomeView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'networth/home.html'

    def test_func(self):
        if self.request.user.is_staff:
            return True
        return False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # for financial report summanry
        financial_data = FinancialData.objects.filter(owner=self.request.user)
        if financial_data.exists():
            context['fd'] = financial_data.latest('date')

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
        fixed_asset = FixedAsset.objects.filter(owner=self.request.user)
        liability = BorrowedFund.objects.filter(owner=self.request.user)

        context['investments'] = investments.order_by('host_country')
        context['savings'] = savings.order_by('value_currency')
        context['stocks'] = stocks.order_by('unit_cost_currency')
        context['business'] = business.order_by('unit_cost_currency')
        context['fixed_asset'] = fixed_asset.order_by('value_currency')
        
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
        
        currencies = business.values_list('unit_cost_currency', flat=True).distinct().order_by('unit_cost_currency')
        business_total = list()
        if currencies.exists():
            for currency in currencies:
                business_total.append(Money(business.filter(unit_cost_currency=currency).annotate(value=F('unit_cost') * F('shares')).aggregate(Sum('value'))['value__sum'], currency))
        context['business_total'] = business_total
        
        currencies = fixed_asset.values_list('value_currency', flat=True).distinct().order_by('value_currency')
        fixed_asset_total = list()
        if currencies.exists():
            for currency in currencies:
                fixed_asset_total.append(Money(fixed_asset.filter(value_currency=currency).aggregate(Sum('value'))['value__sum'], currency))
        context['fixed_asset_total'] = fixed_asset_total

        currencies = liability.values_list('borrowed_amount_currency', flat=True).distinct().order_by('borrowed_amount_currency')
        liability_total = list()
        if currencies.exists():
            for currency in currencies:
                liability_total.append(Money(liability.filter(settlement_amount_currency=currency).aggregate(Sum('settlement_amount'))['settlement_amount__sum'], currency))
        # context['fixed_asset_total'] = liability_total

        
        # financial_report_email()
        # fr = FinancialReport(savings, investments, stocks, business, fixed_asset, liability)
        # context['country_networth'] = fr.country_networth()
        return context

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'networth/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # get the record of the first date of the current year
        current_year = datetime.date.today().year
        qs = FinancialData.objects.filter(owner=self.request.user).filter(date__year=current_year).order_by('date')
        if qs.exists():
            
            obj = qs.filter(date__date=datetime.date(2025, 2, 1)).first() if current_year == 2025 else qs.first()
            base_networth = obj.networth()
            daily_roi = 1.2 * obj.daily_roi # 20% above the first roi of the year

            context['financials'] = {
                'base_networth': base_networth,
                'base_daily_roi': daily_roi,
                'EYEV': 365 * daily_roi + base_networth,
                'EYEP':  format_percent(round((365 * daily_roi)/base_networth, 4), decimal_quantization=False, locale='en_US')
            }
            
            qs = qs.annotate(f_networth = F('worth')-F('liability'))
            max_networth = qs.aggregate(Max('f_networth'))['f_networth__max']
            context['max_networth'] = Money(max_networth, 'USD')
            context['date_max_networth'] = qs.filter(f_networth=max_networth).first().date.date
            context['max_rate'] = ('NGN', max([r[0]['NGN'] for r in qs.values_list('exchange_rate') if r[0] is not None]))
            context['present_growth'] = format_percent(round((qs.latest('date').networth() - base_networth)/base_networth, 5), decimal_quantization=False, locale='en_US')

        cut_off_date = datetime.datetime.now(ZoneInfo('America/Halifax')) - datetime.timedelta(days=7)
        financials = FinancialData.objects.filter(owner=self.request.user).filter(date__gte=cut_off_date).order_by('date')
        
        # get the minimum worth
        if financials:
            min_worth = financials.aggregate(Min('worth'))['worth__min']
            recent_days = [ date.strftime('%m/%d') for date in financials.values_list('date', flat=True) ]
            recent_networth = [ financial.networth().amount for financial in financials ]
            context['networth_image'] = bar_chart(recent_days, recent_networth, 'USD($)', 'Days', 'Networth', y_min=4*min_worth/5)

            min_roi = financials.aggregate(Min('daily_roi'))['daily_roi__min']
            recent_daily_roi = financials.values_list('daily_roi', flat=True)
            context['daily_roi_image'] = bar_chart(recent_days, recent_daily_roi, 'USD($)', 'Days', 'Daily ROI', y_min=int(min_roi/2))

            latest = financials.latest('date')
            labels = ['saving', 'investment', 'stock', 'fixed asset', 'business']
            sizes = [latest.savings.amount, latest.investment.amount, latest.stock.amount, latest.fixed_asset.amount, latest.business.amount]
            context['asset_distribution'] = donut_chart(labels=labels, sizes=sizes)
            labels = latest.networth_by_country.keys()
            sizes = latest.networth_by_country.values()
            
            context['asset_location'] = donut_chart(labels, sizes)
        return context

class InvestmentCreateView(LoginRequiredMixin, FormView):
    form_class = InvestmentCreateForm
    template_name = 'networth/investment_form.html'

    def get_success_url(self):
        return reverse_lazy('networth-home')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['pk'] = self.kwargs.get('pk')
        kwargs['user'] = self.request.user
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
    form_class = InvestmentUpdateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

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
        inv = Investment.objects.get(pk=self.kwargs['pk'])
        inv.rollover(form.cleaned_data['rate'], form.cleaned_data['start_date'], form.cleaned_data['duration'], 
                     form.cleaned_data['option'], form.cleaned_data['adjusted_amount'], form.cleaned_data['savings_account'])
        return super().form_valid(form)

class InvestmentTerminationView(LoginRequiredMixin, FormView):
    # model = Investment
    form_class = InvestmentTerminationForm
    success_url = reverse_lazy('networth-home')
    template_name = 'networth/terminate_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        pk = self.kwargs.get('pk')
        kwargs['pk'] = pk
        return kwargs

    def form_valid(self, form):
        inv = Investment.objects.get(pk=self.kwargs['pk'])
        adjuster = -1 if form.cleaned_data['amount_type'] == 'DR' else 1
        amount = inv.principal + inv.roi() + Money(adjuster * form.cleaned_data['adjusted_amount'], inv.principal.currency)
        inv.terminate(amount, form.cleaned_data['savings_account'], form.cleaned_data['timestamp'])
        messages.success(self.request, "Investment dropped into savings successfully")
        return super().form_valid(form)

class StockCreateView(LoginRequiredMixin, FormView):
    form_class = StockCreateForm
    template_name = 'networth/stock_form.html'
    success_url = reverse_lazy('networth-home')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['pk'] = self.kwargs.get('pk')
        kwargs['user'] = self.request.user
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


# Saving
class SavingCreateView(LoginRequiredMixin, CreateView):
    model = Saving
    form_class = SavingForm
    success_url = reverse_lazy('networth-home')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.owner = self.request.user if self.request.user.is_staff else None
        return super().form_valid(form)

class SavingDetailView(LoginRequiredMixin, DetailView):
    model = Saving

class SavingUpdateView(LoginRequiredMixin, UpdateView):
    model = Saving
    success_url = reverse_lazy('networth-home')
    form_class = SavingFormUpdate

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
# Business
class BusinessCreateView(LoginRequiredMixin, FormView):
    success_url = reverse_lazy('networth-home')
    form_class = BusinessCreateForm
    template_name = 'networth/business_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['pk'] = self.kwargs.get('pk')
        kwargs['user'] = self.request.user
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

# Fixed Asset
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

class FixedAssetDetailView(LoginRequiredMixin, DetailView):
    model = FixedAsset
    template_name = 'networth/fixed_asset_detail.html'

class FixedAssetUpdateView(LoginRequiredMixin, UpdateView):
    model = FixedAsset
    template_name = 'networth/fixed_asset_form.html'
    form_class = FixedAssetUpdateForm
    
    def get_success_url(self):
        return reverse_lazy('networth-fixed-asset', kwargs={'pk': self.object.pk})

# External Funds
class ExternalFundHome(LoginRequiredMixin, ListView):
    model = Saving
    template_name = 'networth/external_fund.html'

class BorrowedFundView(LoginRequiredMixin, FormView):

    template_name = 'networth/borrow_form.html'
    success_url = reverse_lazy('networth-external-fund-home')
    form_class = BorrowedFundForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['pk'] = self.kwargs.get('pk')
        return kwargs
    
    def form_valid(self, form):
        savings_account = form.cleaned_data['savings_account']
        
        savings_account.borrow_fund(form.cleaned_data['source'],
                                    form.cleaned_data['borrowed_amount'],
                                    form.cleaned_data['cost_of_fund'],
                                    form.cleaned_data['date'],

                                )
        messages.success(self.request, 'Transaction is successful !!!')
        return super().form_valid(form)
    
class SavingsCounterTransferView(LoginRequiredMixin, FormView):
    form_class = SavingsCounterTransferForm
    success_url = reverse_lazy('networth-home')
    template_name = 'networth/saving_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['saving_transfer'] = True
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['username'] = self.request.user.username
        return kwargs
    
    def form_valid(self, form):
        receiver: Saving = form.cleaned_data['receiver_account']
        donor = form.cleaned_data['donor_account']
        amount = Money(form.cleaned_data['amount'], donor.value.currency)
        
        receiver.fund_transfer(donor, amount, form.cleaned_data['date'])
        messages.success(self.request, f"Fund moved from {donor} to {receiver} !!!")
        return super().form_valid(form)
    
class InstitutionReportView(LoginRequiredMixin, TemplateView):
    template_name = 'networth/institution.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        investments = Investment.objects.filter(is_active=True).filter(owner=self.request.user).order_by('holder')
        holders_in_investment = investments.values_list('holder', flat=True).distinct()
        dataset = list()
        for holder in holders_in_investment:
            
            # institution = investments.first().holder
            principals = list(obj.principal for obj in investments.filter(holder=holder))
            records = list()
            sub_total = Decimal(0)
            for principal in principals:
                exchange_rate = ExchangeRate.objects.get(target_currency=principal.currency)
                base_amount = principal.amount / Decimal(exchange_rate.rate)
                records.append({
                    'currency': principal.currency,
                    'target_amount': principal,
                    'base_amount': Money(base_amount, 'USD')
                })
                sub_total += base_amount
            dataset.append({
                'holder': holder,
                'records': records,
                'sub_total': Money(sub_total, 'USD')
            })
        context['institutions'] = dataset
        context['total'] = sum(data['sub_total'] for data in dataset)
        return context