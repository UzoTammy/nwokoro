import datetime
import decimal
from zoneinfo import ZoneInfo

from django.utils import timezone
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models.aggregates import Max
from django.db.models import F, ExpressionWrapper, DateField
from django.views.generic import (TemplateView, ListView,  CreateView, DetailView, UpdateView, FormView, RedirectView)
from django.views import View
from django.http import JsonResponse
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# ── DEV ONLY: email preview ──────────────────────────────────────────────────
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string


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
                     BusinessTransaction, BorrowedFundTransaction, StockTransaction, FixedAssetTransaction,
                     ExchangeRate)

from .plots import bar_chart, donut_chart, plot
from .tools import (get_value, valuation, ytd_roi, investments_by_holder,networth_by_currency, currency_list,
                    get_transactions, networth_ratio, number_of_instruments, number_of_assets, 
                    exchange_rate, get_assets_liabilities, set_roi, get_year_financial, current_year_roi,past_investment,
                    AggregatedAsset)


def get_target():
    
    return {
        2025: Money(100_000, 'USD'),
        2026: Money(120_000, 'USD'),
        2027: Money(144_000, 'USD')
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
        exch = exchange_rate('NGN', 'CAD')
        context['exchange'] = f'{exch[0]}/CA$ on {exch[1].strftime("%A %d-%b-%Y")}' if exch else None
            # naira valuation
        naira_valuation = valuation('NGN')
        context['naira_value_comment'] = f"Naira have {naira_valuation[1]} {naira_valuation[0]} since {naira_valuation[2]}"

        # Section 2: Networth and growth
        financial_data = FinancialData.objects.filter(owner=self.request.user)
        if financial_data.exists():
            fd = financial_data.latest('date')
            context['fd'] = fd

        # Section 3: Networth Distribution
        context['donot_networth'] = {
            'labels':['Business', 'Fixed Asset', 'Investment', 'Saving', 'Stock'],
            'values':[float(val) for val in [fd.business.amount,fd.fixed_asset.amount,
                    fd.investment.amount,fd.savings.amount, fd.stock.amount]]}

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
        mature_investment_current_year = current_year_asset.investments()
        ytd_turnover = mature_investment_current_year[0]
        ytd_roi = mature_investment_current_year[1]
        context['mature_investment_current_year_roi'] = ytd_roi
        context['mature_investment_current_year_turnover'] = ytd_turnover

        all_asset = AggregatedAsset(self.request.user)
        mature_investment = all_asset.investments()
        alltime_turnover = mature_investment[0]
        alltime_roi = mature_investment[1]
        context['mature_investment_roi'] = alltime_roi
        context['mature_investment_turnover'] = alltime_turnover

        # Yield percentages (roi / turnover * 100)
        context['ytd_yield_pct'] = (
            round(float(ytd_roi.amount) / float(ytd_turnover.amount) * 100, 1)
            if ytd_turnover.amount else 0
        )
        context['alltime_yield_pct'] = (
            round(float(alltime_roi.amount) / float(alltime_turnover.amount) * 100, 1)
            if alltime_turnover.amount else 0
        )

        # Progress toward full maturity (present_roi / roi)
        if financial_data.exists():
            roi_at_maturity = fd.roi.amount
            context['present_roi_pct'] = (
                round(float(fd.present_roi.amount) / float(roi_at_maturity) * 100, 1)
                if roi_at_maturity else 0
            )
        # Section 6: Plot of investment ROI per month
        months = list(d['month'] for d in current_year_roi(self.request.user))
        values = list(d['amount'].amount for d in current_year_roi(self.request.user))
        # context['plot_investment_earnings'] = bar_chart(months, values, X='Months', Y='Earnings', title='Earnings per month')
        context['investment_earnings'] = {'months': months, 'values': [float(val) for val in values]}
        if not months:
            q1 = decimal.Decimal(0.25)*get_target()[year].amount
            q2 = decimal.Decimal(0.5)*get_target()[year].amount
            q3 = decimal.Decimal(0.75)*get_target()[year].amount
            q4 = get_target()[year].amount
            context['investment_earnings'] = {'months': ['Q1', 'Q2', 'Q3', 'Q4'], 'values': [float(val) for val in [q1, q2, q3, q4]]}
        # Section 7: Recent Transactions
        transactions = [SavingsTransaction, InvestmentTransaction,BusinessTransaction, StockTransaction, 
                        BorrowedFundTransaction, FixedAssetTransaction]
        context['recent_transactions'] = get_transactions(*transactions)
        
        # Section 8: Asset Ratio
        context['asset_ratio'] = networth_ratio(self.request.user, 'NG', 'NGN')
        ar = context['asset_ratio']
        if 'currency' in ar:
            total_amount = ar['currency'].amount + ar['base_value'].amount
            ngn_pct = round(float(ar['currency'].amount) / float(total_amount) * 100, 1) if total_amount else 0
            context['asset_ratio_extra'] = {
                'total': ar['currency'] + ar['base_value'],
                'ngn_pct': ngn_pct,
                'usd_pct': round(100 - ngn_pct, 1),
            }

        # Section 9: Number of Instruments and YTD Reward
            # instruments
        context['number_of_instruments'] = (number_of_instruments(self.request.user.username), number_of_assets(self.request.user.username))
            # Reward
        rewards = RewardFund.objects.filter(owner=self.request.user).filter(date__year=datetime.date.today().year)
        if rewards.exists():
            reward_value = sum(Money(reward.amount.amount/exchange_rate(reward.amount.currency)[0].amount, 'USD') for reward in rewards)
            context['reward'] = reward_value

        return context
    
class NetworthHistoryView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'networth/networth_history.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        records = FinancialData.objects.filter(owner=self.request.user).filter(
            date__date__gte=datetime.date(2025, 1, 29)
        ).order_by('date')
        if not records.exists():
            context['no_data'] = True
            return context

        dates = [r.date.strftime('%d %b %Y') for r in records]
        worths = [float(r.worth.amount) for r in records]
        context['chart_data'] = {'dates': dates, 'worths': worths}

        latest = records.latest('date')
        earliest = records.earliest('date')
        peak = max(records, key=lambda r: r.worth.amount)

        context['latest'] = latest
        context['earliest'] = earliest
        context['peak'] = peak
        context['record_count'] = records.count()
        context['growth'] = latest.worth - earliest.worth

        seen = set()
        quarterly = []
        for r in records.order_by('-date'):
            q_num = (r.date.month - 1) // 3 + 1
            key = (r.date.year, q_num)
            if key not in seen:
                seen.add(key)
                quarterly.append({'record': r, 'label': f'Q{q_num} {r.date.year}'})
        context['quarterly_records'] = quarterly

        return context


class AnnualReportView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'networth/balance_sheet.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        default_year = datetime.date.today().year - 1
        current_year = int(self.request.GET.get('year', default_year))
        context['annum'] = str(current_year)

        fd = FinancialData.objects.filter(owner=self.request.user).filter(date__year=current_year)
        if not fd.exists():
            context['no_data'] = True
            return context

        if current_year == 2025:
            first_fd = fd.filter(date__date=datetime.date(2025, 1, 29)).first() or fd.earliest('date')
        else:
            first_fd = fd.earliest('date')
        last_fd = fd.latest('date')

        context['balance_brought_forward'] = first_fd.worth
        context['opening_date'] = first_fd.date
        context['closing_date'] = last_fd.date

        turnover = AggregatedAsset(self.request.user, current_year)
        all_assets = [turnover.investments(), turnover.real_estate(), turnover.business(), turnover.stock()]

        context['turnover'] = {
            'investment': all_assets[0],
            'fixed_asset': all_assets[1],
            'business': all_assets[2],
            'stock': all_assets[3],
        }

        rewards = RewardFund.objects.filter(owner=self.request.user).filter(date__year=current_year)
        reward_value = Money(0, 'USD')
        if rewards.exists():
            reward_value = sum(
                Money(r.amount.amount / exchange_rate(r.amount.currency)[0].amount, 'USD')
                for r in rewards
            )

        stream_changes = {
            # Add reward_value back to neutralise its silent deduction from savings.
            # Reward already reduced Saving.value (and therefore last_fd.savings), so
            # without this correction it would be counted twice — once here and once
            # as the explicit "Less Reward" line in the reconciliation.
            'savings':     last_fd.savings     - first_fd.savings + reward_value,
            'investment':  last_fd.investment  - first_fd.investment  - all_assets[0][1],
            'fixed_asset': last_fd.fixed_asset - first_fd.fixed_asset - all_assets[1][1],
            'business':    last_fd.business    - first_fd.business    - all_assets[2][1],
            'stock':       last_fd.stock       - first_fd.stock       - all_assets[3][1],
            'liability':   last_fd.liability   - first_fd.liability,
            'reward':      reward_value,
        }
        context['income_change'] = stream_changes

        all_asset_total = sum(a[1] for a in all_assets)
        changes_total = sum([
            stream_changes['savings'],
            stream_changes['investment'],
            stream_changes['fixed_asset'],
            stream_changes['business'],
            stream_changes['stock'],
            -stream_changes['liability'],
        ])
        context['earnings_total'] = all_asset_total
        context['stream_changes_total'] = changes_total

        gross_networth = first_fd.worth + all_asset_total + changes_total
        context['gross_networth'] = gross_networth
        context['less_reward'] = reward_value
        context['net_networth'] = gross_networth - reward_value
        context['current_networth'] = last_fd.worth

        # Year navigation
        available_years = sorted({
            d.year for d in FinancialData.objects.filter(owner=self.request.user).dates('date', 'year')
        }, reverse=True)
        context['available_years'] = available_years
        context['current_year_val'] = current_year
        context['prev_year'] = str(current_year - 1) if (current_year - 1) in available_years else None
        context['next_year'] = str(current_year + 1) if (current_year + 1) in available_years else None

        return context
    
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'networth/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # get the record of the first date of the current year
        current_year = timezone.now().year
        financial_data = get_year_financial(self.request.user, year=current_year)
        # taken care of negative edge cases
        if not financial_data.exists():
            current_year -= 1
            financial_data = get_year_financial(self.request.user, year=current_year)
            if not financial_data.exists():
                context['no_financial_data'] = True
        # end of -ve edge cases

        if financial_data.exists():
            
            obj = financial_data.filter(date__date=datetime.date(2025, 2, 1)).first() if current_year == 2025 else financial_data.first()
            base_networth = obj.worth
            target = get_target().get(current_year) # set target 
            daily_roi = set_roi(target)

            # Section 1: Base Networth and Projections
            context['base_networth'] =  base_networth
            context['base_daily_roi'] = daily_roi
            context['projected_networth'] =  target + base_networth
            context['projected_growth'] =  format_percent(round(target/base_networth, 4), decimal_quantization=False, locale='en_US')

            # Section 2: Actual Networth and growth rate
            fd = FinancialData.objects.filter(owner=self.request.user).filter(date__year=current_year)
            fd = fd.latest('date') if fd.exists() else None
            year_end_networth = Money(0, 'USD') if fd is None else fd.worth
            context['year_end_networth'] = year_end_networth
            context['growth'] = year_end_networth-base_networth
            context['growth_rate'] = round(100*(year_end_networth-base_networth)/year_end_networth, 2)
            
            # Section 3, 4, 5: Visuals
            start_date = datetime.datetime.now(ZoneInfo('America/Halifax')) - datetime.timedelta(days=7) # 7 days ago
            financials = FinancialData.objects.filter(owner=self.request.user).filter(date__gte=start_date).order_by('date')

            if not financials.exists():
                financials = FinancialData.objects.filter(owner=self.request.user)
            
            # get the minimum worth
            if financials.exists():
                recent_days = [ date.strftime('%m/%d') for date in financials.values_list('date', flat=True) ]
                recent_networth = [ financial.worth.amount for financial in financials ]
                # Section 3: 
                context['networth_trend_for_chart'] = {'days': recent_days, 'networth': [float(val) for val in recent_networth]}
                
                latest = financials.latest('date')
                labels = latest.networth_by_country.keys()
                sizes = latest.networth_by_country.values()
                # context['asset_location'] = donut_chart(labels, sizes)
                context['networth_by_country'] = {'labels': list(labels), 'values': list(sizes)}
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
                    y_axes.append([round(f[currency]/factor, 3) for f in qs.values_list('exchange_rate', flat=True)])
                else:
                    y_axes.append([round(f[currency], 3) for f in qs.values_list('exchange_rate', flat=True)])
              
            context['exchange_rate_trend'] = {
                'dates': dates, 
                'Y1': y_axes[0], 
                'Y2': y_axes[1],
                'labelY1': f'{currency_pair[0]}/$',
                'labelY2': f'x{factor}{currency_pair[1]}/$'
            }
            
            # Section: 
            context['ytd_roi'] = ytd_roi(self.request.user, current_year)
            context['ytd_roi_prev'] = ytd_roi(self.request.user, current_year-1)
            context['ytd_roi_next'] = ytd_roi(self.request.user, current_year+1)
            
            # total of investments
            context['ytd_roi_total_current_year'] = get_ytd_roi_total(self.request.user, current_year)
            context['ytd_roi_total_prev_year'] = get_ytd_roi_total(self.request.user, current_year-1)
            context['ytd_roi_total_next_year'] = get_ytd_roi_total(self.request.user, current_year+1)
            
        return context

class TransactionListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'networth/transaction_list.html'

    def test_func(self):
        if self.request.user.is_staff:
            return True
        return False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        transactions = [SavingsTransaction, InvestmentTransaction,BusinessTransaction, StockTransaction, 
                        BorrowedFundTransaction, FixedAssetTransaction]
        
        context['transactions'] = get_transactions(*transactions, period='year')
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
            if fd.worth.amount > 0:
                context['savings_pct'] = round((fd.savings.amount / fd.worth.amount) * 100, 1)

        savings = get_assets_liabilities(owner=self.request.user)['savings'].annotate(
            last_transaction=Max('savings_transactions__timestamp')
        )

        context['savings'] = savings.order_by('value_currency')
        context['to_usd_total'] = sum(saving.to_usd() for saving in savings)

        def _to_usd_amount(obj):
            if obj.value.currency != 'USD':
                return obj.value.amount / exchange_rate(obj.value.currency)[0].amount
            return obj.value.amount

        currencies = savings.values_list('value_currency', flat=True).distinct()
        context['savings_by_currency'] = [
            {'currency': cur, 'usd_value': Money(sum(_to_usd_amount(obj) for obj in savings.filter(value_currency=cur)), 'USD')}
            for cur in currencies
        ]

        holders = savings.values_list('holder', flat=True).distinct()
        savings_summary = []
        for holder in holders:
            qs = savings.filter(holder=holder)
            value = sum(_to_usd_amount(obj) for obj in qs)
            if value > 0:
                savings_summary.append({
                    'holder': holder,
                    'usd_value': Money(value, 'USD'),
                })
        context['savings_summary'] = savings_summary

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
        
        context['investments'] = sorted([investment for investment in investments], key=lambda x: x.maturity())
        context['investment_count'] = investments.count()
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
        return super().form_valid(form)

class SavingDetailView(LoginRequiredMixin, DetailView):
    model = Saving

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transactions'] = SavingsTransaction.objects.filter(savings__id=self.object.pk).order_by('-timestamp')[:10]
        return context


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
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        default_year = datetime.date.today().year - 1
        current_year = int(self.request.GET.get('year', default_year))
        context['report_year'] = str(current_year)
        context['generated_on'] = datetime.date.today().strftime('%d %b, %Y')

        record = FinancialData.objects.filter(owner=self.request.user).filter(date__year=current_year)
        if not record.exists():
            context['no_data'] = True
            return context

        if current_year == 2025:
            first_record = record.filter(date__date=datetime.date(2025, 1, 29)).first() or record.earliest('date')
        else:
            first_record = record.earliest('date')
        fd = record.latest('date')
        first_worth = first_record.worth
        growth = fd.worth - first_worth

        growth_percent = format_percent(
            round(growth / first_worth, 4), decimal_quantization=False, locale='en_US'
        ) if first_worth.amount else '0%'

        target_roi = get_target().get(current_year)
        if target_roi:
            base_daily_roi = set_roi(target_roi)
            expected_growth_rate = format_percent(
                round(target_roi / first_worth, 4), decimal_quantization=False, locale='en_US'
            )
        else:
            base_daily_roi = None
            expected_growth_rate = None

        context['fd_first'] = {
            'worth': first_worth,
            'date': first_record.date.strftime('%d %b, %Y'),
            'growth': growth,
            'growth_percent': growth_percent,
            'base_daily_roi': base_daily_roi,
            'target_roi': target_roi,
            'expected_growth_rate': expected_growth_rate,
            'record': first_record,
        }
        context['fd'] = fd

        # Charts
        context['plot'] = bar_chart(
            ['Fixed Asset', 'Stock', 'Investment', 'Savings', 'Business'],
            [fd.fixed_asset.amount, fd.stock.amount, fd.investment.amount, fd.savings.amount, fd.business.amount],
            'Worth', 'Instrument Type', 'Worth Distribution'
        )
        can = fd.networth_by_country.get('CA', 0)
        ngn = fd.networth_by_country.get('NG', 0)
        usa = fd.networth_by_country.get('US', 0)
        context['donot'] = donut_chart(['CAN', 'NGN', 'USA'], [can, ngn, usa])

        # Networth by country (readable)
        context['networth_by_country'] = fd.networth_by_country

        # Exchange rates (readable pairs)
        if fd.exchange_rate:
            context['exchange_rates'] = [
                {'currency': k, 'rate': round(v, 4)}
                for k, v in fd.exchange_rate.items()
            ]

        # Reward withdrawn this year
        rewards = RewardFund.objects.filter(owner=self.request.user).filter(date__year=current_year)
        reward_value = Money(0, 'USD')
        if rewards.exists():
            reward_value = sum(
                Money(r.amount.amount / exchange_rate(r.amount.currency)[0].amount, 'USD')
                for r in rewards
            )
        context['reward_value'] = reward_value

        # Asset changes (closing minus opening per class)
        context['asset_changes'] = {
            'savings':     fd.savings     - first_record.savings,
            'investment':  fd.investment  - first_record.investment,
            'stock':       fd.stock       - first_record.stock,
            'business':    fd.business    - first_record.business,
            'fixed_asset': fd.fixed_asset - first_record.fixed_asset,
            'liability':   fd.liability   - first_record.liability,
        }

        # Investment ROI by currency (page 2)
        context['ytd_roi'] = ytd_roi(self.request.user, current_year)

        # Networth by currency (page 2)
        networth_currency = []
        for cur in currency_list(self.request.user):
            value = networth_by_currency(cur, self.request.user)
            rate = exchange_rate(cur)[0]
            networth_currency.append({
                'currency': cur,
                'value_usd': Money(value / rate.amount, 'USD'),
            })
        context['networth_by_currency'] = networth_currency

        # Quarterly networth progression (page 2)
        seen_q, quarterly = set(), []
        for r in record.order_by('-date'):
            q_num = (r.date.month - 1) // 3 + 1
            key = (r.date.year, q_num)
            if key not in seen_q:
                seen_q.add(key)
                quarterly.append({'label': f'Q{q_num} {r.date.year}', 'record': r})
        context['quarterly_progression'] = quarterly

        return context


def email_report_preview(request):
    if not settings.DEBUG:
        from django.http import Http404
        raise Http404

    ctx = {
        'owner': request.user if request.user.is_authenticated else 'John Doe',
        'networth':          Money(142_850.00, 'USD'),
        'savings':           Money(28_500.00,  'USD'),
        'investments':       Money(55_200.00,  'USD'),
        'stocks':            Money(19_750.00,  'USD'),
        'business':          Money(24_400.00,  'USD'),
        'fixed_asset':       Money(32_000.00,  'USD'),
        'liability':         Money(17_000.00,  'USD'),
        'roi':               Money(6_340.00,   'USD'),
        'daily_roi':         Money(17.37,       'USD'),
        'present_roi':       Money(2_210.50,   'USD'),
        'prev_networth':     Money(139_620.00, 'USD'),
        'change_in_networth':Money(3_230.00,   'USD'),
        'is_gain':           True,
        'exchange_rate':     'NGN 1,620.00/CA$',
    }
    html = render_to_string('networth/mails/financial_report.html', ctx, request=request)
    return HttpResponse(html)


class ForecastView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'networth/forecast.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = datetime.date.today()

        latest_fd = FinancialData.objects.filter(owner=user).order_by('-date').first()
        if not latest_fd:
            context['no_data'] = True
            return context

        rates = {er.target_currency: er.rate for er in ExchangeRate.objects.all()}
        def to_usd(money_obj):
            rate = rates.get(str(money_obj.currency), 1)
            return float(money_obj.amount) / float(rate)

        # Historical chart: snapshots from Jan 1 of current year to today
        year_start = datetime.date(today.year, 1, 1)
        hist_fd = FinancialData.objects.filter(
            owner=user, date__date__gte=year_start
        ).order_by('date')
        hist_labels = [fd.date.strftime('%b %d') for fd in hist_fd]
        hist_values = [round(float(fd.worth.amount), 2) for fd in hist_fd]

        # Forecast baseline: latest FinancialData snapshot — consistent with the chart's last point
        current_savings_usd   = float(latest_fd.savings.amount)
        current_inv_usd       = float(latest_fd.investment.amount)
        current_stock_usd     = float(latest_fd.stock.amount)
        current_business_usd  = float(latest_fd.business.amount)
        current_fa_usd        = float(latest_fd.fixed_asset.amount)
        current_liability_usd = float(latest_fd.liability.amount)
        current_nw            = float(latest_fd.worth.amount)

        # Live investment list for avg rate and inv_table only
        investments = list(Investment.objects.filter(owner=user))

        # Average rate from matured investments; fall back to active if none matured
        matured = [inv for inv in investments if inv.due_in_days() <= 0]
        if matured:
            avg_inv_rate = round(sum(inv.rate for inv in matured) / len(matured), 2)
        else:
            active = [inv for inv in investments if inv.is_active]
            avg_inv_rate = round(sum(inv.rate for inv in active) / len(active), 2) if active else 0.0

        active_investments = [inv for inv in investments if inv.is_active]

        current_snap = {
            'savings':     round(current_savings_usd, 2),
            'investment':  round(current_inv_usd, 2),
            'stock':       round(current_stock_usd, 2),
            'business':    round(current_business_usd, 2),
            'fixed_asset': round(current_fa_usd, 2),
            'liability':   round(current_liability_usd, 2),
            'worth':       round(current_nw, 2),
        }

        def compound(principal, annual_rate_pct, months):
            return principal * (1 + annual_rate_pct / 100) ** (months / 12)

        default_months = 12
        default_rate   = 20.0
        proj_inv  = compound(current_inv_usd,      avg_inv_rate, default_months)
        proj_stk  = compound(current_stock_usd,    default_rate, default_months)
        proj_biz  = compound(current_business_usd, default_rate, default_months)
        proj_fa   = compound(current_fa_usd,        default_rate, default_months)
        proj_nw   = current_savings_usd + proj_inv + proj_stk + proj_biz + proj_fa - current_liability_usd
        proj_gain = proj_nw - current_nw
        proj_gain_pct = round(proj_gain / current_nw * 100, 1) if current_nw else 0

        default_forecast = {
            'networth':    round(proj_nw, 0),
            'gain':        round(proj_gain, 0),
            'gain_pct':    proj_gain_pct,
            'investment':  round(proj_inv, 0),
            'inv_gain':    round(proj_inv - current_inv_usd, 0),
            'stock':       round(proj_stk, 0),
            'business':    round(proj_biz, 0),
            'fixed_asset': round(proj_fa, 0),
            'savings':     round(current_savings_usd, 0),
            'liability':   round(current_liability_usd, 0),
        }

        # Investment detail table (active only)
        inv_table = []
        for inv in active_investments:
            principal_usd   = to_usd(inv.principal)
            roi_total_usd   = to_usd(inv.roi())
            roi_present_usd = to_usd(inv.present_roi())
            inv_table.append({
                'holder':                inv.holder,
                'principal':             inv.principal,
                'rate':                  inv.rate,
                'maturity':              inv.maturity(),
                'due_in_days':           inv.due_in_days(),
                'roi_total_usd':         round(roi_total_usd, 2),
                'roi_remaining_usd':     round(roi_total_usd - roi_present_usd, 2),
                'total_at_maturity_usd': round(principal_usd + roi_total_usd, 2),
            })

        context.update({
            'hist_labels':      hist_labels,
            'hist_values':      hist_values,
            'inv_table':        inv_table,
            'avg_inv_rate':     avg_inv_rate,
            'current_snap':     current_snap,
            'default_forecast': default_forecast,
            'today':            today,
        })
        return context


class ForecastPDFView(LoginRequiredMixin, UserPassesTestMixin, WeasyTemplateResponseMixin, TemplateView):
    template_name = 'networth/forecast_pdf.html'
    pdf_attachment = True

    def test_func(self):
        return self.request.user.is_staff

    @property
    def pdf_filename(self):
        today = datetime.date.today()
        return f'forecast_report_{today.strftime("%Y%m%d")}.pdf'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user    = self.request.user
        today   = datetime.date.today()

        # ── Read GET parameters ───────────────────────────────────────────────
        def safe_float(key, default):
            try:    return float(self.request.GET.get(key, default))
            except: return float(default)

        months     = max(1, int(safe_float('months', 12)))
        rate_stock = safe_float('rate_stock', 20)
        rate_biz   = safe_float('rate_biz',   20)
        rate_fa    = safe_float('rate_fa',    20)

        latest_fd = FinancialData.objects.filter(owner=user).order_by('-date').first()
        if not latest_fd:
            context['no_data'] = True
            return context

        rates = {er.target_currency: er.rate for er in ExchangeRate.objects.all()}
        def to_usd(money_obj):
            rate = rates.get(str(money_obj.currency), 1)
            return float(money_obj.amount) / float(rate)

        # ── Baseline (latest FinancialData snapshot) ──────────────────────────
        b_sav  = float(latest_fd.savings.amount)
        b_inv  = float(latest_fd.investment.amount)
        b_stk  = float(latest_fd.stock.amount)
        b_biz  = float(latest_fd.business.amount)
        b_fa   = float(latest_fd.fixed_asset.amount)
        b_liab = float(latest_fd.liability.amount)
        b_nw   = float(latest_fd.worth.amount)

        # ── Avg investment rate ───────────────────────────────────────────────
        investments = list(Investment.objects.filter(owner=user))
        matured     = [inv for inv in investments if inv.due_in_days() <= 0]
        if matured:
            avg_inv_rate = round(sum(inv.rate for inv in matured) / len(matured), 2)
        else:
            active_inv = [inv for inv in investments if inv.is_active]
            avg_inv_rate = round(sum(inv.rate for inv in active_inv) / len(active_inv), 2) if active_inv else 0.0

        # ── Compound growth ───────────────────────────────────────────────────
        def compound(principal, annual_rate_pct, m):
            return principal * (1 + annual_rate_pct / 100) ** (m / 12)

        p_inv  = compound(b_inv,  avg_inv_rate, months)
        p_stk  = compound(b_stk,  rate_stock,   months)
        p_biz  = compound(b_biz,  rate_biz,     months)
        p_fa   = compound(b_fa,   rate_fa,      months)
        p_nw   = b_sav + p_inv + p_stk + p_biz + p_fa - b_liab
        p_gain = p_nw - b_nw
        p_gain_pct = round(p_gain / b_nw * 100, 2) if b_nw else 0

        # ── Expected end date ─────────────────────────────────────────────────
        import calendar
        raw_month = today.month + months
        end_year  = today.year + (raw_month - 1) // 12
        end_month = (raw_month - 1) % 12 + 1
        end_day   = min(today.day, calendar.monthrange(end_year, end_month)[1])
        end_date  = datetime.date(end_year, end_month, end_day)

        # ── Month-by-month milestone table ───────────────────────────────────
        milestones = []
        step = max(1, months // 6)          # up to ~6 rows
        for m in list(range(step, months, step)) + [months]:
            raw = today.month + m
            yr  = today.year + (raw - 1) // 12
            mo  = (raw - 1) % 12 + 1
            dy  = min(today.day, calendar.monthrange(yr, mo)[1])
            nw  = (b_sav
                   + compound(b_inv, avg_inv_rate, m)
                   + compound(b_stk, rate_stock, m)
                   + compound(b_biz, rate_biz, m)
                   + compound(b_fa,  rate_fa, m)
                   - b_liab)
            milestones.append({
                'date':    datetime.date(yr, mo, dy).strftime('%b %Y'),
                'months':  m,
                'networth': round(nw, 2),
                'gain':     round(nw - b_nw, 2),
            })

        # ── Active investment table ───────────────────────────────────────────
        inv_table = []
        for inv in [i for i in investments if i.is_active]:
            pu  = to_usd(inv.principal)
            rtu = to_usd(inv.roi())
            rpu = to_usd(inv.present_roi())
            inv_table.append({
                'holder':         inv.holder,
                'principal':      inv.principal,
                'rate':           inv.rate,
                'maturity':       inv.maturity(),
                'due_in_days':    inv.due_in_days(),
                'roi_total':      round(rtu, 2),
                'roi_remaining':  round(rtu - rpu, 2),
                'total_maturity': round(pu + rtu, 2),
            })

        context.update({
            'report_date':   today,
            'start_date':    today,
            'end_date':      end_date,
            'months':        months,
            'user':          user,
            'growth_rates': {
                'investment':  avg_inv_rate,
                'stock':       rate_stock,
                'business':    rate_biz,
                'fixed_asset': rate_fa,
            },
            'current': {
                'savings':     round(b_sav,  2),
                'investment':  round(b_inv,  2),
                'stock':       round(b_stk,  2),
                'business':    round(b_biz,  2),
                'fixed_asset': round(b_fa,   2),
                'liability':   round(b_liab, 2),
                'networth':    round(b_nw,   2),
            },
            'projected': {
                'savings':     round(b_sav,  2),
                'investment':  round(p_inv,  2),
                'stock':       round(p_stk,  2),
                'business':    round(p_biz,  2),
                'fixed_asset': round(p_fa,   2),
                'liability':   round(b_liab, 2),
                'networth':    round(p_nw,   2),
                'gain':        round(p_gain, 2),
                'gain_pct':    p_gain_pct,
            },
            'milestones':  milestones,
            'inv_table':   inv_table,
            'avg_inv_rate': avg_inv_rate,
        })
        return context


class ForecastEmailView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Generate the forecast PDF and deliver it to the user's email address."""

    def test_func(self):
        return self.request.user.is_staff

    def get(self, request, *args, **kwargs):
        import weasyprint

        user = request.user
        if not user.email:
            return JsonResponse({'status': 'error', 'message': 'No email address is linked to your account.'}, status=400)

        # Build context via ForecastPDFView (reuse its get_context_data)
        pdf_view = ForecastPDFView()
        pdf_view.request = request
        pdf_view.args    = args
        pdf_view.kwargs  = kwargs
        ctx = pdf_view.get_context_data()

        if ctx.get('no_data'):
            return JsonResponse({'status': 'error', 'message': 'No financial data available.'}, status=400)

        # Render HTML → PDF bytes
        html_string = render_to_string('networth/forecast_pdf.html', ctx, request=request)
        try:
            pdf_bytes = weasyprint.HTML(
                string=html_string,
                base_url=request.build_absolute_uri('/')
            ).write_pdf()
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'PDF generation failed: {e}'}, status=500)

        # Compose and send email
        today    = datetime.date.today()
        months   = ctx['months']
        end_date = ctx['end_date']
        subject  = f'Net Worth Forecast Report — {today.strftime("%d %b %Y")}'
        body     = (
            f'Dear {user.username},\n\n'
            f'Please find attached your {months}-month net worth forecast report.\n\n'
            f'  • Report date : {today.strftime("%d %B %Y")}\n'
            f'  • Target date : {end_date.strftime("%d %B %Y")}\n'
            f'  • Current NW  : ${ctx["current"]["networth"]:,.2f}\n'
            f'  • Projected NW: ${ctx["projected"]["networth"]:,.2f}\n'
            f'  • Net Growth  : +${ctx["projected"]["gain"]:,.2f} ({ctx["projected"]["gain_pct"]}%)\n\n'
            f'This is a projection based on the assumptions in the attached report.\n\n'
            f'Best regards'
        )
        filename = f'forecast_report_{today.strftime("%Y%m%d")}.pdf'

        try:
            msg = EmailMessage(subject=subject, body=body, to=[user.email])
            msg.attach(filename, pdf_bytes, 'application/pdf')
            msg.send()
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Email delivery failed: {e}'}, status=500)

        return JsonResponse({'status': 'ok', 'message': f'Report sent to {user.email}'})
