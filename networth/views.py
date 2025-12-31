import datetime
import decimal
from zoneinfo import ZoneInfo

from django.utils import timezone
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models.aggregates import Max
from django.db.models import F
from django.views.generic import (TemplateView, ListView,  CreateView, DetailView, UpdateView, FormView, RedirectView)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from babel.numbers import format_percent
from djmoney.models.fields import Money
from django_weasyprint import WeasyTemplateResponseMixin

from .forms import (InvestmentCreateForm, InvestmentUpdateForm, StockCreateForm, StockUpdateForm, SavingForm, SavingFormUpdate,
                    InvestmentRolloverForm, InvestmentTerminationForm, BusinessCreateForm, BusinessUpdateForm, 
                    FixedAssetCreateForm, FixedAssetUpdateForm, FixedAssetRentForm, FixedAssetCollectRentForm,
                    SavingsCounterTransferForm, 
                    #BusinessPlowBackForm, 
                    BusinessLiquidateForm,BorrowedFundForm, 
                    ReCapitalizeForm,
                    ConversionForm, RewardFundForm, InjectFundForm, LiabilityRepayForm)

from .models import (Saving, Stock, Investment, Business, FinancialData, FixedAsset, Rent,
                     RewardFund, InjectFund, BorrowedFund, SavingsTransaction, InvestmentTransaction,
                     BusinessTransaction, BorrowedFundTransaction, StockTransaction, FixedAssetTransaction)

from .plots import bar_chart, donut_chart, plot
from .tools import (get_value, valuation, ytd_roi, investments_by_holder,networth_by_currency, currency_list,
                    recent_transactions, networth_ratio, number_of_instruments, number_of_assets, 
                    exchange_rate, get_assets_liabilities, set_roi, get_year_financial, current_year_roi,past_investment,
                    AggregatedAsset)

def get_target():
    
    return {
        2025: Money(100_100, 'USD'),
        2026: Money(100_100, 'USD')
    }

def is_homogenous(value: list):
    if not value:
        return False
    if len(value) == 1:
        return False
    if len(value) == 2 and value[0] != value[1]:
        return False
    return True
    
def highest_occurring_item(value: list):
    result = list()
    items = set(value)
    for item in items:
        result.append((item, value.count(item)))
    return max(result, key=lambda x: x[1])[0]

def get_ytd_roi_total(user, year):
    data = ytd_roi(user, year)
    cad_p, ngn_p, usd_p = data['CAD']['principal'], data['NGN']['principal'], data['USD']['principal']
    cad_roi, ngn_roi, usd_roi = data['CAD']['roi'], data['NGN']['roi'], data['USD']['roi']

    ytd_roi_principal_total = cad_p/exchange_rate('CAD')[0]+ngn_p/exchange_rate('NGN')[0]+usd_p.amount
    ytd_roi_total = cad_roi/exchange_rate('CAD')[0]+ngn_roi/exchange_rate('NGN')[0]+usd_roi.amount
    
    return {'principal': ytd_roi_principal_total, 'roi': ytd_roi_total, 
            'percent': 100*ytd_roi_total/ytd_roi_principal_total if ytd_roi_principal_total else 0}
    
# Create your views here.
class NetworthHomeView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'networth/home.html'

    def test_func(self):
        if self.request.user.is_staff:
            return True
        return False
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Section 1: Message box   
        # exchange
        exch = exchange_rate('NGN', 'CAD')
        rate = exch[0]
        context['exchange'] = f'{rate}/CA$ on {exch[1].strftime("%A %d-%b-%Y")}'

        # naira valuation
        naira_valuation = valuation('NGN')
        context['naira_value_comment'] = f"Naira have {naira_valuation[1]} {naira_valuation[0]} since {naira_valuation[2]}"

        # Section 2: Networth 
        financial_data = FinancialData.objects.filter(owner=self.request.user)
        if financial_data.exists():
            fd = financial_data.latest('date')
            context['fd'] = fd 

        # Section 3: Networth Distribution
        context['donot_networth'] = donut_chart(
            ['Business', 'Fixed Asset', 'Investment', 'Saving', 'Stock'], 
            [fd.business.amount,
             fd.fixed_asset.amount,
             fd.investment.amount,
             fd.savings.amount,
             fd.stock.amount]
        )

        # Section 4: Networth by country and currency
        networth_currency = list()

        for currency in currency_list(self.request.user):
            value = networth_by_currency(currency, self.request.user)
            networth_currency.append(
                {
                    'currency': currency,
                    'value': Money(value, currency),
                    'value_usd': Money(value/exchange_rate(currency)[0].amount, 'USD')
                }
            )
        context['networth_by_currency'] = networth_currency

        # Section 5: Investment Score
        year = timezone.now().year
        current_year_asset = AggregatedAsset(self.request.user, year)
        investments = Investment.objects.filter(owner=current_year_asset.owner).filter(is_active=False)
        
        mature_investment_current_year = current_year_asset.investments(investments)
        context['mature_investment_current_year_roi'] = mature_investment_current_year[1] 
        context['mature_investment_current_year_turnover'] = mature_investment_current_year[0]

        all_asset = AggregatedAsset(self.request.user)
        mature_investment = all_asset.investments(investments)
        context['mature_investment_roi'] = mature_investment[1]
        context['mature_investment_turnover'] = mature_investment[0]
        
        # Section 6: Plot of investment ROI per month
        months = list(d['month'] for d in current_year_roi(self.request.user))
        values = list(d['amount'].amount for d in current_year_roi(self.request.user))
        context['plot_investment_earnings'] = bar_chart(months, values, X='Months', Y='Earnings', title='Earnings per month')

        # Section 7: Recent Transactions
        transactions = [SavingsTransaction, InvestmentTransaction,BusinessTransaction, StockTransaction, 
                        BorrowedFundTransaction, FixedAssetTransaction]
        context['recent_transactions'] = recent_transactions(*transactions)
        
        # Section 8: Asset Ratio
        context['asset_ratio'] = networth_ratio(self.request.user, 'NG', 'NGN')

        # Section 9: Number of Instruments and YTD Reward
            # instruments
        context['number_of_instruments'] = (number_of_instruments(self.request.user.username), number_of_assets(self.request.user.username))
            # Reward
        rewards = RewardFund.objects.filter(owner=self.request.user).filter(date__year=datetime.date.today().year)
        if rewards.exists():
            reward_value = sum(Money(reward.amount.amount/exchange_rate(reward.amount.currency)[0].amount, 'USD') for reward in rewards)
            context['reward'] = reward_value

        return context
    
class BalanceSheetView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'networth/balance_sheet.html'

    def test_func(self):
        if self.request.user.is_staff:
            return True
        return False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        current_year = datetime.date.today().year
        fd = FinancialData.objects.filter(owner=self.request.user).filter(date__year=current_year)
        first_fd = fd.filter(date__date=datetime.date(2025, 2, 1)).first() if current_year == 2025 else fd.first()
        last_fd = fd.latest('date')
            
        context['balance_brought_forward'] = first_fd.worth

        turnover = AggregatedAsset(current_year, self.request.user)
        all_assets = [turnover.investment(), turnover.real_estate(), turnover.business(), turnover.stock()]
                
        context['turnover'] = {
            'investment': all_assets[0],
            'fixed_asset': all_assets[1],
            'business': all_assets[2],
            'stock': all_assets[3]
        }

        rewards = RewardFund.objects.filter(owner=self.request.user).filter(date__year=datetime.date.today().year)
        reward_value = Money(0, 'USD')
        if rewards.exists():
            reward_value = sum(Money(reward.amount.amount/exchange_rate(reward.amount.currency)[0].amount, 'USD') for reward in rewards)
        
        stream_changes = {
            'savings': last_fd.savings - first_fd.savings,
            'investment': last_fd.investment - first_fd.investment - all_assets[0][1],
            'fixed_asset': last_fd.fixed_asset - first_fd.fixed_asset - all_assets[1][1],
            'business': last_fd.business - first_fd.business - all_assets[2][1],
            'stock': last_fd.stock - first_fd.stock - all_assets[3][1],
            'liability': last_fd.liability - first_fd.liability,
            'reward': reward_value
        }
        context['income_change'] = stream_changes
        
        all_asset_total = all_assets[0][1] + all_assets[1][1] + all_assets[2][1] + all_assets[3][1]
        changes_total = sum([stream_changes['savings'], stream_changes['investment'], stream_changes['fixed_asset'], stream_changes['business'], 
                            stream_changes['stock'], -stream_changes['liability']])
        context['stream_changes_total'] = changes_total
        context['earnings_total'] = all_asset_total
        context['balance_1'] = first_fd.worth + all_asset_total + changes_total

        second_fd = FinancialData.objects.filter(owner=self.request.user).filter(date__year=current_year).last()
        context['current_networth'] = second_fd.worth
        return context
    
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'networth/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # get the record of the first date of the current year
        current_year = datetime.date.today().year
        financial_data = get_year_financial(self.request.user)

        if financial_data.exists():
            
            obj = financial_data.filter(date__date=datetime.date(2025, 2, 1)).first() if current_year == 2025 else financial_data.first()
            base_networth = obj.networth()
            target = get_target().get(datetime.date.today().year) # set target 
            daily_roi = set_roi(target)

            #Section 1: Base Networth and Projections
            context['base_networth'] =  base_networth
            context['base_daily_roi'] = daily_roi
            context['projected_networth'] =  target + base_networth
            context['projected_growth'] =  format_percent(round(target/base_networth, 4), decimal_quantization=False, locale='en_US')

            # Section 2: Actual Networth and growth rate
            current_year = timezone.now().year
            fd = FinancialData.objects.filter(owner=self.request.user).filter(date__year=current_year)
            fd = fd.latest('date') if fd.exists() else None
            year_end_networth = Money(0, 'USD') if fd is None else fd.networth()
            context['year_end_networth'] = year_end_networth
            context['growth'] = year_end_networth-base_networth
            context['growth_rate'] = round(100*(year_end_networth-base_networth)/year_end_networth, 2)
            
            start_date = datetime.datetime.now(ZoneInfo('America/Halifax')) - datetime.timedelta(days=7)
            financials = FinancialData.objects.filter(owner=self.request.user).filter(date__gte=start_date).order_by('date')

            if not financials.exists():
                financials = FinancialData.objects.filter(owner=self.request.user)
            
            # get the minimum worth
            if financials.exists():
                recent_days = [ date.strftime('%m/%d') for date in financials.values_list('date', flat=True) ]
                recent_networth = [ financial.worth.amount for financial in financials ]
                context['networth_image'] = plot(recent_days, recent_networth, Y1='USD($)', X=f"mm/dd/{start_date.strftime('%Y')}", title='Networth Trend')

                latest = financials.latest('date')
                labels = latest.networth_by_country.keys()
                sizes = latest.networth_by_country.values()
                context['asset_location'] = donut_chart(labels, sizes)
        
            qs = financials.exclude(exchange_rate=None)

            dates = [ date.strftime('%m/%d') for date in qs.values_list('date', flat=True) ]
            y_axes = list()
            currency_pair = list(currency_list(self.request.user))
            if 'USD' in currency_pair:
                currency_pair.remove('USD') 

            # you need currency pair factor
            factor = 1000
            for currency in currency_pair:
                if currency == 'NGN':
                    y_axes.append([f[currency]/factor for f in qs.values_list('exchange_rate', flat=True)])
                else:
                    y_axes.append([f[currency] for f in qs.values_list('exchange_rate', flat=True)])
              
            context['daily_roi_image'] = plot(dates, y_axis1=y_axes[0], y_axis2=y_axes[1], Y1=f'{currency_pair[0]}/$', Y2=f'x{factor}{currency_pair[1]}/$', X='Days', title='One week exchange rate trend')

            # Section: 
            context['ytd_roi'] = ytd_roi(self.request.user, current_year)
            context['ytd_roi_prev'] = ytd_roi(self.request.user, current_year-1)
            context['ytd_roi_next'] = ytd_roi(self.request.user, current_year+1)
            # total of investments
            context['ytd_roi_total_current_year'] = get_ytd_roi_total(self.request.user, current_year)
            context['ytd_roi_total_prev_year'] = get_ytd_roi_total(self.request.user, current_year-1)
            context['ytd_roi_total_next_year'] = get_ytd_roi_total(self.request.user, current_year+1)
            
        return context

class SavingListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'networth/saving_list.html'

    def test_func(self):
        if self.request.user.is_staff:
            return True
        return False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # for financial report summanry
        financial_data = FinancialData.objects.filter(owner=self.request.user)
        if financial_data.exists():
            fd = financial_data.latest('date')
            context['fd'] = fd

        savings = get_assets_liabilities(owner=self.request.user)['savings']
        
        context['savings'] = savings.order_by('value_currency')
        context['savings_total'] = get_value(savings, 'saving')
        context['to_usd_total'] = sum(saving.to_usd() for saving in savings)

        holders = savings.values_list('holder', flat=True).distinct()
        savings_summary = list()
        for holder in holders:
            qs = savings.filter(holder=holder)
            value = decimal.Decimal('0')
            for obj in qs:
                if obj.value.currency != 'USD':
                    value += obj.value.amount/exchange_rate(obj.value.currency)[0].amount 
                else:
                    value += obj.value.amount
            savings_summary.append({
                'holder': obj.holder,
                'usd_value': Money(value, 'USD')
            })
        context['savings_summary'] = savings_summary
        
        return context

class InvestmentListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'networth/investment_list.html'

    def test_func(self):
        if self.request.user.is_staff:
            return True
        return False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # for financial report summanry
        financial_data = FinancialData.objects.filter(owner=self.request.user)
        if financial_data.exists():
            fd = financial_data.latest('date')
            context['fd'] = fd

        investments = get_assets_liabilities(owner=self.request.user)['investments']
        context['investments'] = investments.order_by('principal')
        context['investment_total'] = get_value(investments, 'investment')
        context['to_usd_total'] = sum(investment.to_usd() for investment in investments)

        holders = investments.values_list('holder', flat=True).distinct()
        investments_summary = list()
        for holder in holders:
            value = decimal.Decimal('0')
            qs = investments.filter(holder=holder)
            for obj in qs:
                if obj.principal.currency != 'USD':
                    value += obj.principal.amount/exchange_rate(obj.principal.currency)[0].amount 
                else:
                    value += obj.principal.amount
            investments_summary.append({
                'holder': obj.holder,
                'value': Money(value, 'USD')
            })
        context['investments_summary'] = investments_summary
        
        context['year_roi'] = ytd_roi(self.request.user, datetime.date.today().year)

        return context
    
class StockListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'networth/stock_list.html'

    def test_func(self):
        if self.request.user.is_staff:
            return True
        return False
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # for financial report summanry
        financial_data = FinancialData.objects.filter(owner=self.request.user)
        if financial_data.exists():
            fd = financial_data.latest('date')
            context['fd'] = fd

        
        # fetch assets of current logged-in user
        stocks = get_assets_liabilities(owner=self.request.user)['stocks']
        
        context['stocks'] = stocks.order_by('unit_cost_currency')
        
        # Asset total
        context['stock_total'] = get_value(stocks, 'stock')
        context['to_usd_total'] = sum(stock.to_usd() for stock in stocks)
        return context


class BusinessListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'networth/business_list.html'

    def test_func(self):
        if self.request.user.is_staff:
            return True
        return False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # for financial report summanry
        financial_data = FinancialData.objects.filter(owner=self.request.user)
        if financial_data.exists():
            fd = financial_data.latest('date')
            context['fd'] = fd

        business = get_assets_liabilities(owner=self.request.user)['business']
        context['business'] = business.order_by('unit_cost_currency')
        
        context['business_total'] = get_value(business, 'business')
        context['to_usd_total'] = sum(biz.to_usd() for biz in business)
        
        return context

class FixedAssetListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'networth/fixed_asset_list.html' 

    def test_func(self):
        if self.request.user.is_staff:
            return True
        return False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # for financial report summanry
        financial_data = FinancialData.objects.filter(owner=self.request.user)
        if financial_data.exists():
            fd = financial_data.latest('date')
            context['fd'] = fd

        fixed_asset = get_assets_liabilities(owner=self.request.user)['fixed_asset']
        context['fixed_asset'] = fixed_asset.order_by('value_currency')
        
        context['fixed_asset_total'] = get_value(fixed_asset, 'asset')
        context['to_usd_total'] = sum(fa.to_usd() for fa in fixed_asset)
        return context

class LiabilityListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'networth/liability_list.html'   

    def test_func(self):
        if self.request.user.is_staff:
            return True
        return False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # for financial report summanry
        financial_data = FinancialData.objects.filter(owner=self.request.user)
        if financial_data.exists():
            fd = financial_data.latest('date')
            context['fd'] = fd

        liabilities = get_assets_liabilities(owner=self.request.user)['liabilities']
        context['liabilities'] = liabilities.order_by('host_country')
        context['liabilities_total'] = get_value(liabilities, 'liability')
        context['to_usd_total'] = sum(liability.to_usd() for liability in liabilities)
        return context

#Investment
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
        start_date = form.cleaned_data['start_date']
        
        dt = datetime.datetime.combine(start_date, datetime.time.min)
        tz = ZoneInfo("UTC")
        aware_date = dt.replace(tzinfo=tz)
        savings_account.create_investment(
            holder=form.cleaned_data['holder_select'] if form.cleaned_data['holder_select'] else form.cleaned_data['holder_text'],
            principal=form.cleaned_data['principal'],
            rate=form.cleaned_data['rate'],
            start_date=aware_date,
            duration=form.cleaned_data['duration'],
            category=form.cleaned_data['category']
        )
        print(dt, aware_date)
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

# stock
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
        form.instance.holder = form.cleaned_data['holder_text'] if form.cleaned_data['holder_text'] != '' else form.cleaned_data['holder_select']
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

class SavingsConversionView(LoginRequiredMixin, FormView):
    success_url = reverse_lazy('networth-home')
    form_class = ConversionForm
    template_name = 'networth/conversion_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['username'] = self.request.user.username
        return kwargs

    def form_valid(self, form):
        source:Saving = form.cleaned_data['source_account']
        receiver = form.cleaned_data['receiver_account']
        amount = form.cleaned_data['amount']
        converted_amount = form.cleaned_data['converted_amount']
        source.convert_fund(receiver, amount, converted_amount)
        messages.success(self.request, "Fund conversion complete !!!")
        return super().form_valid(form) 
    
# Business
class BusinessCreateView(LoginRequiredMixin, FormView):
    success_url = reverse_lazy('networth-home')
    form_class = BusinessCreateForm
    template_name = 'networth/business_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Establish a Business'
        return context

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

class BusinessLiquidateView(LoginRequiredMixin, FormView):
    template_name = 'networth/liquidate_form.html'
    form_class = BusinessLiquidateForm
    
    def get_success_url(self):
        return reverse('networth-business-detail', kwargs={'pk': self.kwargs['pk']})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['pk'] = self.kwargs.get('pk')
        return kwargs
    
    def form_valid(self, form):
        business = Business.objects.get(pk=self.kwargs['pk'])
        business.liquidate(**form.cleaned_data)
        messages.success(self.request, "Liquidation complete, proceed to recapitalize !!!")
        return super().form_valid(form)

class BusinessReCapitalizeView(LoginRequiredMixin, FormView):
    template_name = 'networth/business_form.html'
    form_class = ReCapitalizeForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Business Recapitalization'
        context['business'] = Business.objects.get(pk=self.kwargs['pk'])
        return context

    def get_success_url(self):
        return reverse_lazy('networth-home')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['pk'] = self.kwargs.get('pk')
        return kwargs
    
    def form_valid(self, form):
        business = Business.objects.get(pk=self.kwargs['pk'])
        business.re_capitalize(**form.cleaned_data)
        
        return super().form_valid(form)
    
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # rent_obj = self.request.GET['rent'] == 'show' or 'rent' not in self.request.GET
        # context['show_rent_obj'] = rent_obj
        return context

class FixedAssetUpdateView(LoginRequiredMixin, UpdateView):
    model = FixedAsset
    template_name = 'networth/fixed_asset_form.html'
    form_class = FixedAssetUpdateForm
    
    def get_success_url(self):
        return reverse_lazy('networth-fixed-asset', kwargs={'pk': self.object.pk})

class FixedAssetRentView(LoginRequiredMixin, FormView):
    template_name = 'networth/rent_form.html'
    form_class = FixedAssetRentForm

    def get_success_url(self):
        return reverse('networth-fixed-asset-detail', kwargs={'pk': self.kwargs['pk']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Rent'
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['pk'] = self.kwargs.get('pk')
        return kwargs

    def form_valid(self, form):
        fixed_asset = FixedAsset.objects.get(pk=self.kwargs['pk'])
        fixed_asset.create_rent(**form.cleaned_data)
        messages.success(self.request, 'Rent is successfully created !!!')
        return super().form_valid(form)

class FixedAssetCollectRentView(LoginRequiredMixin, FormView):
    form_class = FixedAssetCollectRentForm
    template_name = 'networth/rent_form.html'

    def get_success_url(self):
        return reverse('networth-fixed-asset-detail', kwargs={'pk': self.kwargs['pk']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Collect Rent'
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['pk'] = self.kwargs.get('pk')
        return kwargs
    
    def form_valid(self, form):
        fixed_asset = FixedAsset.objects.get(pk=self.kwargs['pk'])
        fixed_asset.collect_rent(form.cleaned_data['savings_account'])
        messages.success(self.request, 'Rent collected successfully !!!')
        return super().form_valid(form)

class FixedAssetStopRentView(LoginRequiredMixin, RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        fixed_asset = FixedAsset.objects.get(pk=kwargs['pk'])
        fixed_asset.stop_rent()
        messages.success(self.request, 'Rent is stopped successfully !!!')
        return reverse('networth-fixed-asset-detail', kwargs={'pk': kwargs['pk']})

class FixedAssetRestoreRentView(LoginRequiredMixin, RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        fixed_asset = FixedAsset.objects.get(pk=kwargs['pk'])
        fixed_asset.restore_rent()
        messages.success(self.request, 'Rent is restored successfully !!!')
        return reverse('networth-fixed-asset-detail', kwargs={'pk': kwargs['pk']})

class FixedAssetUpdateRentView(LoginRequiredMixin, UpdateView):
    model = Rent
    form_class = FixedAssetRentForm
    pk_url_kwarg = 'rent_pk'
    
    def get_success_url(self):
        return reverse('networth-fixed-asset-detail', kwargs={'pk': self.kwargs['pk']})

# liability
class LiabilityDetailView(LoginRequiredMixin, DetailView):
    model = BorrowedFund
    template_name = 'networth/liability_detail.html'

class LiabilityUpdateView(LoginRequiredMixin, UpdateView):
    model = BorrowedFund
    template_name = 'networth/borrow_form.html'
    form_class = BorrowedFundForm

    def get_success_url(self):
        url = reverse('networth-liability-detail', kwargs={'pk': self.kwargs['pk']})
        return url

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        borrowedfund = BorrowedFund.objects.get(pk=self.kwargs.get('pk'))
        kwargs['pk'] = borrowedfund.savings_account.pk
        return kwargs
    
class LiabilityRepayView(LoginRequiredMixin, FormView):
    # model = BorrowedFund
    template_name = 'networth/repay_form.html'
    form_class = LiabilityRepayForm

    def get_success_url(self):
        return reverse('networth-liability-detail', kwargs={'pk': self.kwargs['pk']})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        borrowedfund = BorrowedFund.objects.get(pk=self.kwargs.get('pk'))
        kwargs['pk'] = borrowedfund.pk
        return kwargs
    
    def form_valid(self, form):
        bf = BorrowedFund.objects.get(pk=self.kwargs['pk'])

        bf.repay(
            form.cleaned_data['amount'],
            form.cleaned_data['description'],
            form.cleaned_data['date'],
            form.cleaned_data['savings_account']
        )
        messages.success(self.request, f"Repayment made from {form.cleaned_data['savings_account']}")
        return super().form_valid(form)
    
# External Funds
class ExternalFundHome(LoginRequiredMixin, ListView):
    model = Saving
    template_name = 'networth/external_fund.html'

    def post(self, request, *args, **kwargs):
        
        if not('radioAction' in request.POST and 'radioSaving' in request.POST):
            messages.info(request, "You must choose Action to take and Saving Account to proceed")
            return super().get(request, *args, **kwargs)
        
        if request.POST['radioAction'] == 'borrow':
            reverse_url = reverse('networth-borrow-fund', kwargs={'pk': request.POST['radioSaving']})
        elif request.POST['radioAction'] == 'reward':
            reverse_url = reverse("networth-reward-fund", kwargs={'pk': request.POST['radioSaving']})  
        else:
            reverse_url = reverse("networth-inject-fund", kwargs={'pk': request.POST['radioSaving']})  
        return redirect(reverse_url)

class RewardFundView(LoginRequiredMixin, FormView):
    model = RewardFund
    success_url = reverse_lazy('networth-external-fund-home')
    form_class = RewardFundForm
    template_name = 'networth/reward_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['pk'] = self.kwargs.get('pk')
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['account_value'] = Saving.objects.get(pk=self.kwargs['pk']).value
        return context
    
    def form_valid(self, form):
        form.instance.savings_account = Saving.objects.get(pk=self.kwargs['pk'])
        form.instance.owner = form.instance.savings_account.owner
        form.instance.savings_transaction()
        messages.success(self.request, 'Fund withdrawal is successfully !!!')
        form.instance.save()
        return super().form_valid(form)

class InjectFundView(LoginRequiredMixin, FormView):
    model = InjectFund
    success_url = reverse_lazy('networth-external-fund-home')
    form_class = InjectFundForm
    template_name = 'networth/inject_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['pk'] = self.kwargs.get('pk')
        return kwargs
    
    def form_valid(self, form):
        form.instance.savings_account = Saving.objects.get(pk=self.kwargs['pk'])
        form.instance.owner = self.request.user
        form.instance.savings_transaction()
        messages.success(self.request, 'Fund injection is successfully !!!')
        form.instance.save()
        return super().form_valid(form)
        
class BorrowedFundView(LoginRequiredMixin, FormView):
    model = BorrowedFund
    template_name = 'networth/borrow_form.html'
    success_url = reverse_lazy('networth-external-fund-home')
    form_class = BorrowedFundForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['pk'] = self.kwargs.get('pk')
        return kwargs
    
    def form_valid(self, form):
        savings_account = form.cleaned_data['savings_account']
        form.instance.savings_account = savings_account
        form.instance.owner = savings_account.owner
        
        savings_account.borrow(form.cleaned_data['source'],
                                form.cleaned_data['borrowed_amount'],
                                form.cleaned_data['settlement_amount'],
                                form.cleaned_data['date'],
                                form.cleaned_data['terminal_date'],
                                form.cleaned_data['description']
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
        context['institutions'] = investments_by_holder(self.request.user)
        return context
    
class PDFNetworthReport(WeasyTemplateResponseMixin, UserPassesTestMixin, TemplateView):
    template_name = 'networth/pdf/networth.html'
    header_html = None

    def test_func(self):
        if self.request.user.is_staff:
            return True
        return False
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_year = datetime.date.today().year
        record = FinancialData.objects.filter(owner=self.request.user).filter(date__year=current_year)
        first_record = record.earliest('date') if current_year != 2025 else record.filter(date__date=datetime.date(2025, 2, 1)).first()
        first_worth = first_record.networth()
        target_roi = Money(100000, 'USD')
        base_daily_roi = set_roi(target_roi)  # 20% above the first roi of the year
        first_date = datetime.date(year=current_year, month=1, day=1).strftime("%d %b, %Y")
        
        fd = record.latest('date')
        growth_percent = format_percent(round((fd.networth() - first_worth)/first_worth, 4), decimal_quantization=False, locale='en_US')
        expected_growth_rate = format_percent(round((target_roi)/first_worth, 4), decimal_quantization=False, locale='en_US')
        
        context['fd_first'] = {'worth': first_worth, 'date': first_date, 'growth': fd.networth() - first_worth,
                               'base_daily_roi': base_daily_roi, 'target_roi': target_roi, 'record': first_record,
                               'growth_percent': growth_percent, 'expected_growth_rate': expected_growth_rate}
        context['fd'] = fd
        context['plot'] = bar_chart(['Fixed Asset', 'Stock', 'Investment', 'Savings',  'Business'], 
                                    [fd.fixed_asset.amount, fd.stock.amount, fd.investment.amount, fd.savings.amount, fd.business.amount],
                                    "Worth", "Instrument Type", "Worth Distribution")
        can = fd.networth_by_country.get('CA', 0)
        ngn = fd.networth_by_country.get('NG', 0)
        usa = fd.networth_by_country.get('US', 0)
        
        context['donot'] = donut_chart(["CAN", "NGN", "USA"], 
                                       [can, ngn, usa])
        
        return context

           