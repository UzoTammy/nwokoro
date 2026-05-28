import datetime

from django.views.generic import TemplateView
from django.views import View
from django.http import JsonResponse
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from djmoney.models.fields import Money
from django_weasyprint import WeasyTemplateResponseMixin

from account.models import Preference
from ..models import FinancialData, Investment, ExchangeRate


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

        year_start = datetime.date(today.year, 1, 1)
        hist_fd = FinancialData.objects.filter(
            owner=user, date__date__gte=year_start
        ).order_by('date')
        hist_labels = [fd.date.strftime('%b %d') for fd in hist_fd]
        hist_values = [round(float(fd.worth.amount), 2) for fd in hist_fd]

        current_savings_usd   = float(latest_fd.savings.amount)
        current_inv_usd       = float(latest_fd.investment.amount)
        current_stock_usd     = float(latest_fd.stock.amount)
        current_business_usd  = float(latest_fd.business.amount)
        current_fa_usd        = float(latest_fd.fixed_asset.amount)
        current_liability_usd = float(latest_fd.liability.amount)
        current_nw            = float(latest_fd.worth.amount)

        investments = list(Investment.objects.filter(owner=user))

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

        pref, _ = Preference.objects.get_or_create(user=user)
        default_months   = pref.forecast_period_months
        default_rate_stk = float(pref.forecast_rate_stock)
        default_rate_biz = float(pref.forecast_rate_business)
        default_rate_fa  = float(pref.forecast_rate_fixed_asset)

        proj_inv  = compound(current_inv_usd,      avg_inv_rate,    default_months)
        proj_stk  = compound(current_stock_usd,    default_rate_stk, default_months)
        proj_biz  = compound(current_business_usd, default_rate_biz, default_months)
        proj_fa   = compound(current_fa_usd,        default_rate_fa,  default_months)
        proj_nw   = current_savings_usd + proj_inv + proj_stk + proj_biz + proj_fa - current_liability_usd
        proj_gain = proj_nw - current_nw
        proj_gain_pct = round(proj_gain / current_nw * 100, 1) if current_nw else 0

        default_forecast = {
            'networth':   round(proj_nw, 0),
            'gain':       round(proj_gain, 0),
            'gain_pct':   proj_gain_pct,
            'investment': round(proj_inv, 0),
            'inv_gain':   round(proj_inv - current_inv_usd, 0),
            'stock':      round(proj_stk, 0),
            'business':   round(proj_biz, 0),
            'fixed_asset': round(proj_fa, 0),
            'savings':    round(current_savings_usd, 0),
            'liability':  round(current_liability_usd, 0),
        }

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
            'pref_months':      default_months,
            'pref_rate_stock':  default_rate_stk,
            'pref_rate_biz':    default_rate_biz,
            'pref_rate_fa':     default_rate_fa,
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
        user  = self.request.user
        today = datetime.date.today()

        pref, _ = Preference.objects.get_or_create(user=user)

        def safe_float(key, default):
            try:    return float(self.request.GET.get(key, default))
            except: return float(default)

        months     = max(1, int(safe_float('months',     pref.forecast_period_months)))
        rate_stock = safe_float('rate_stock', float(pref.forecast_rate_stock))
        rate_biz   = safe_float('rate_biz',   float(pref.forecast_rate_business))
        rate_fa    = safe_float('rate_fa',     float(pref.forecast_rate_fixed_asset))

        latest_fd = FinancialData.objects.filter(owner=user).order_by('-date').first()
        if not latest_fd:
            context['no_data'] = True
            return context

        rates = {er.target_currency: er.rate for er in ExchangeRate.objects.all()}

        def to_usd(money_obj):
            rate = rates.get(str(money_obj.currency), 1)
            return float(money_obj.amount) / float(rate)

        b_sav  = float(latest_fd.savings.amount)
        b_inv  = float(latest_fd.investment.amount)
        b_stk  = float(latest_fd.stock.amount)
        b_biz  = float(latest_fd.business.amount)
        b_fa   = float(latest_fd.fixed_asset.amount)
        b_liab = float(latest_fd.liability.amount)
        b_nw   = float(latest_fd.worth.amount)

        investments = list(Investment.objects.filter(owner=user))
        matured     = [inv for inv in investments if inv.due_in_days() <= 0]
        if matured:
            avg_inv_rate = round(sum(inv.rate for inv in matured) / len(matured), 2)
        else:
            active_inv = [inv for inv in investments if inv.is_active]
            avg_inv_rate = round(sum(inv.rate for inv in active_inv) / len(active_inv), 2) if active_inv else 0.0

        def compound(principal, annual_rate_pct, m):
            return principal * (1 + annual_rate_pct / 100) ** (m / 12)

        p_inv  = compound(b_inv,  avg_inv_rate, months)
        p_stk  = compound(b_stk,  rate_stock,   months)
        p_biz  = compound(b_biz,  rate_biz,     months)
        p_fa   = compound(b_fa,   rate_fa,      months)
        p_nw   = b_sav + p_inv + p_stk + p_biz + p_fa - b_liab
        p_gain = p_nw - b_nw
        p_gain_pct = round(p_gain / b_nw * 100, 2) if b_nw else 0

        import calendar
        raw_month = today.month + months
        end_year  = today.year + (raw_month - 1) // 12
        end_month = (raw_month - 1) % 12 + 1
        end_day   = min(today.day, calendar.monthrange(end_year, end_month)[1])
        end_date  = datetime.date(end_year, end_month, end_day)

        milestones = []
        step = max(1, months // 6)
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
                'date':     datetime.date(yr, mo, dy).strftime('%b %Y'),
                'months':   m,
                'networth': round(nw, 2),
                'gain':     round(nw - b_nw, 2),
            })

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
            'report_date':  today,
            'start_date':   today,
            'end_date':     end_date,
            'months':       months,
            'user':         user,
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
            'milestones':   milestones,
            'inv_table':    inv_table,
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

        pdf_view = ForecastPDFView()
        pdf_view.request = request
        pdf_view.args    = args
        pdf_view.kwargs  = kwargs
        ctx = pdf_view.get_context_data()

        if ctx.get('no_data'):
            return JsonResponse({'status': 'error', 'message': 'No financial data available.'}, status=400)

        html_string = render_to_string('networth/forecast_pdf.html', ctx, request=request)
        try:
            pdf_bytes = weasyprint.HTML(
                string=html_string,
                base_url=request.build_absolute_uri('/')
            ).write_pdf()
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'PDF generation failed: {e}'}, status=500)

        today    = datetime.date.today()
        months   = ctx['months']
        end_date = ctx['end_date']
        subject  = f'Net Worth Forecast Report — {today.strftime("%d %b %Y")}'
        body = (
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
