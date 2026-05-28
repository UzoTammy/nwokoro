import datetime
import decimal
from zoneinfo import ZoneInfo

from django.utils import timezone
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from babel.numbers import format_percent
from djmoney.models.fields import Money

from ..models import (
    FinancialData, RewardFund,
    SavingsTransaction, InvestmentTransaction, BusinessTransaction,
    BorrowedFundTransaction, StockTransaction, FixedAssetTransaction,
)
from ..tools import (
    valuation, ytd_roi, networth_by_currency, currency_list,
    get_transactions, networth_ratio, number_of_instruments, number_of_assets,
    exchange_rate, set_roi, get_year_financial, current_year_roi, AggregatedAsset,
)


def get_target():
    return {
        2025: Money(100_000, 'USD'),
        2026: Money(120_000, 'USD'),
        2027: Money(144_000, 'USD'),
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

    ytd_roi_principal_total = cad_p / exchange_rate('CAD')[0] + ngn_p / exchange_rate('NGN')[0] + usd_p.amount
    ytd_roi_total = cad_roi / exchange_rate('CAD')[0] + ngn_roi / exchange_rate('NGN')[0] + usd_roi.amount

    return {
        'principal': ytd_roi_principal_total,
        'roi': ytd_roi_total,
        'percent': 100 * ytd_roi_total / ytd_roi_principal_total if ytd_roi_principal_total else 0,
    }


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
        naira_valuation = valuation('NGN')
        context['naira_value_comment'] = f"Naira have {naira_valuation[1]} {naira_valuation[0]} since {naira_valuation[2]}"

        # Section 2: Networth and growth
        financial_data = FinancialData.objects.filter(owner=self.request.user)
        if financial_data.exists():
            fd = financial_data.latest('date')
            context['fd'] = fd

        # Section 3: Networth Distribution
        context['donot_networth'] = {
            'labels': ['Business', 'Fixed Asset', 'Investment', 'Saving', 'Stock'],
            'values': [float(val) for val in [fd.business.amount, fd.fixed_asset.amount,
                       fd.investment.amount, fd.savings.amount, fd.stock.amount]],
        }

        # Section 4: Networth by country and currency
        networth_currency = list()
        for currency in currency_list(self.request.user):
            value = networth_by_currency(currency, self.request.user)
            networth_currency.append({
                'currency': currency,
                'value': Money(value, currency),
                'value_usd': Money(value / exchange_rate(currency)[0].amount, 'USD'),
            })
        context['networth_by_currency'] = networth_currency

        # Section 5: Investment Score
        year = timezone.now().year
        current_year_asset = AggregatedAsset(self.request.user, year)
        mature_investment_current_year = current_year_asset.investments()
        ytd_turnover = mature_investment_current_year[0]
        ytd_roi_val = mature_investment_current_year[1]
        context['mature_investment_current_year_roi'] = ytd_roi_val
        context['mature_investment_current_year_turnover'] = ytd_turnover

        all_asset = AggregatedAsset(self.request.user)
        mature_investment = all_asset.investments()
        alltime_turnover = mature_investment[0]
        alltime_roi = mature_investment[1]
        context['mature_investment_roi'] = alltime_roi
        context['mature_investment_turnover'] = alltime_turnover

        context['ytd_yield_pct'] = (
            round(float(ytd_roi_val.amount) / float(ytd_turnover.amount) * 100, 1)
            if ytd_turnover.amount else 0
        )
        context['alltime_yield_pct'] = (
            round(float(alltime_roi.amount) / float(alltime_turnover.amount) * 100, 1)
            if alltime_turnover.amount else 0
        )

        if financial_data.exists():
            roi_at_maturity = fd.roi.amount
            context['present_roi_pct'] = (
                round(float(fd.present_roi.amount) / float(roi_at_maturity) * 100, 1)
                if roi_at_maturity else 0
            )

        # Section 6: Plot of investment ROI per month
        months = list(d['month'] for d in current_year_roi(self.request.user))
        values = list(d['amount'].amount for d in current_year_roi(self.request.user))
        context['investment_earnings'] = {'months': months, 'values': [float(val) for val in values]}
        if not months:
            q1 = decimal.Decimal(0.25) * get_target()[year].amount
            q2 = decimal.Decimal(0.5) * get_target()[year].amount
            q3 = decimal.Decimal(0.75) * get_target()[year].amount
            q4 = get_target()[year].amount
            context['investment_earnings'] = {
                'months': ['Q1', 'Q2', 'Q3', 'Q4'],
                'values': [float(val) for val in [q1, q2, q3, q4]],
            }

        # Section 7: Recent Transactions
        transactions = [
            SavingsTransaction, InvestmentTransaction, BusinessTransaction,
            StockTransaction, BorrowedFundTransaction, FixedAssetTransaction,
        ]
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
        context['number_of_instruments'] = (
            number_of_instruments(self.request.user.username),
            number_of_assets(self.request.user.username),
        )
        rewards = RewardFund.objects.filter(owner=self.request.user).filter(date__year=datetime.date.today().year)
        if rewards.exists():
            reward_value = sum(
                Money(reward.amount.amount / exchange_rate(reward.amount.currency)[0].amount, 'USD')
                for reward in rewards
            )
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


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'networth/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_year = timezone.now().year
        financial_data = get_year_financial(self.request.user, year=current_year)
        if not financial_data.exists():
            current_year -= 1
            financial_data = get_year_financial(self.request.user, year=current_year)
            if not financial_data.exists():
                context['no_financial_data'] = True

        if financial_data.exists():
            obj = financial_data.filter(date__date=datetime.date(2025, 2, 1)).first() if current_year == 2025 else financial_data.first()
            base_networth = obj.worth
            target = get_target().get(current_year)
            daily_roi = set_roi(target)

            context['base_networth'] = base_networth
            context['base_daily_roi'] = daily_roi
            context['projected_networth'] = target + base_networth
            context['projected_growth'] = format_percent(round(target / base_networth, 4), decimal_quantization=False, locale='en_US')

            fd = FinancialData.objects.filter(owner=self.request.user).filter(date__year=current_year)
            fd = fd.latest('date') if fd.exists() else None
            year_end_networth = Money(0, 'USD') if fd is None else fd.worth
            context['year_end_networth'] = year_end_networth
            context['growth'] = year_end_networth - base_networth
            context['growth_rate'] = round(100 * (year_end_networth - base_networth) / year_end_networth, 2)

            start_date = datetime.datetime.now(ZoneInfo('America/Halifax')) - datetime.timedelta(days=7)
            financials = FinancialData.objects.filter(owner=self.request.user, date__gte=start_date).order_by('date')

            if not financials.exists():
                financials = FinancialData.objects.filter(owner=self.request.user).order_by('date')

            if financials.exists():
                # cap chart data to the 7 most recent records
                chart_records = list(financials.order_by('-date')[:7])[::-1]
                recent_days = [f.date.strftime('%m/%d') for f in chart_records]
                recent_networth = [float(f.worth.amount) for f in chart_records]
                context['networth_trend_for_chart'] = {'days': recent_days, 'networth': recent_networth}

                latest = financials.latest('date')
                labels = latest.networth_by_country.keys()
                sizes = latest.networth_by_country.values()
                context['networth_by_country'] = {'labels': list(labels), 'values': list(sizes)}

            # cap exchange rate chart to 7 most recent records that have rate data
            chart_qs = list(financials.exclude(exchange_rate=None).order_by('-date')[:7])[::-1]
            dates = [f.date.strftime('%m/%d') for f in chart_qs]
            y_axes = list()
            currency_pair = list(currency_list(self.request.user))
            if 'USD' in currency_pair:
                currency_pair.remove('USD')

            factor = 1000
            for currency in currency_pair:
                if currency == 'NGN':
                    y_axes.append([round(f.exchange_rate[currency] / factor, 3) for f in chart_qs])
                else:
                    y_axes.append([round(f.exchange_rate[currency], 3) for f in chart_qs])

            context['exchange_rate_trend'] = {
                'dates': dates,
                'Y1': y_axes[0],
                'Y2': y_axes[1],
                'labelY1': f'{currency_pair[0]}/$',
                'labelY2': f'x{factor}{currency_pair[1]}/$',
            }

            context['ytd_roi'] = ytd_roi(self.request.user, current_year)
            context['ytd_roi_prev'] = ytd_roi(self.request.user, current_year - 1)
            context['ytd_roi_next'] = ytd_roi(self.request.user, current_year + 1)

            context['ytd_roi_total_current_year'] = get_ytd_roi_total(self.request.user, current_year)
            context['ytd_roi_total_prev_year'] = get_ytd_roi_total(self.request.user, current_year - 1)
            context['ytd_roi_total_next_year'] = get_ytd_roi_total(self.request.user, current_year + 1)

        return context


class TransactionListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'networth/transaction_list.html'

    def test_func(self):
        if self.request.user.is_staff:
            return True
        return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transactions = [
            SavingsTransaction, InvestmentTransaction, BusinessTransaction,
            StockTransaction, BorrowedFundTransaction, FixedAssetTransaction,
        ]
        context['transactions'] = get_transactions(*transactions, period='year')
        return context
