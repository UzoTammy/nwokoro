import datetime

from django.conf import settings
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.template.loader import render_to_string

from babel.numbers import format_percent
from djmoney.models.fields import Money
from django_weasyprint import WeasyTemplateResponseMixin

from ..models import FinancialData, RewardFund
from ..plots import bar_chart, donut_chart
from ..tools import (
    investments_by_holder, ytd_roi, networth_by_currency, currency_list,
    exchange_rate, AggregatedAsset, set_roi,
)
from .dashboard import get_target


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

        available_years = sorted({
            d.year for d in FinancialData.objects.filter(owner=self.request.user).dates('date', 'year')
        }, reverse=True)
        context['available_years'] = available_years
        context['current_year_val'] = current_year
        context['prev_year'] = str(current_year - 1) if (current_year - 1) in available_years else None
        context['next_year'] = str(current_year + 1) if (current_year + 1) in available_years else None

        return context


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

        context['plot'] = bar_chart(
            ['Fixed Asset', 'Stock', 'Investment', 'Savings', 'Business'],
            [fd.fixed_asset.amount, fd.stock.amount, fd.investment.amount, fd.savings.amount, fd.business.amount],
            'Worth', 'Instrument Type', 'Worth Distribution',
        )
        can = fd.networth_by_country.get('CA', 0)
        ngn = fd.networth_by_country.get('NG', 0)
        usa = fd.networth_by_country.get('US', 0)
        context['donot'] = donut_chart(['CAN', 'NGN', 'USA'], [can, ngn, usa])

        context['networth_by_country'] = fd.networth_by_country

        if fd.exchange_rate:
            context['exchange_rates'] = [
                {'currency': k, 'rate': round(v, 4)}
                for k, v in fd.exchange_rate.items()
            ]

        rewards = RewardFund.objects.filter(owner=self.request.user).filter(date__year=current_year)
        reward_value = Money(0, 'USD')
        if rewards.exists():
            reward_value = sum(
                Money(r.amount.amount / exchange_rate(r.amount.currency)[0].amount, 'USD')
                for r in rewards
            )
        context['reward_value'] = reward_value

        context['asset_changes'] = {
            'savings':     fd.savings     - first_record.savings,
            'investment':  fd.investment  - first_record.investment,
            'stock':       fd.stock       - first_record.stock,
            'business':    fd.business    - first_record.business,
            'fixed_asset': fd.fixed_asset - first_record.fixed_asset,
            'liability':   fd.liability   - first_record.liability,
        }

        context['ytd_roi'] = ytd_roi(self.request.user, current_year)

        networth_currency = []
        for cur in currency_list(self.request.user):
            value = networth_by_currency(cur, self.request.user)
            rate = exchange_rate(cur)[0]
            networth_currency.append({
                'currency': cur,
                'value_usd': Money(value / rate.amount, 'USD'),
            })
        context['networth_by_currency'] = networth_currency

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
        'networth':           Money(142_850.00, 'USD'),
        'savings':            Money(28_500.00,  'USD'),
        'investments':        Money(55_200.00,  'USD'),
        'stocks':             Money(19_750.00,  'USD'),
        'business':           Money(24_400.00,  'USD'),
        'fixed_asset':        Money(32_000.00,  'USD'),
        'liability':          Money(17_000.00,  'USD'),
        'roi':                Money(6_340.00,   'USD'),
        'daily_roi':          Money(17.37,       'USD'),
        'present_roi':        Money(2_210.50,   'USD'),
        'prev_networth':      Money(139_620.00, 'USD'),
        'change_in_networth': Money(3_230.00,   'USD'),
        'is_gain':            True,
        'exchange_rate':      'NGN 1,620.00/CA$',
    }
    html = render_to_string('networth/mails/financial_report.html', ctx, request=request)
    return HttpResponse(html)
