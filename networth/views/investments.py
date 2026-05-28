import datetime
import decimal
from zoneinfo import ZoneInfo

from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import TemplateView, DetailView, UpdateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from djmoney.models.fields import Money

from ..forms import InvestmentCreateForm, InvestmentUpdateForm, InvestmentRolloverForm, InvestmentTerminationForm
from ..models import Saving, Investment, FinancialData
from ..tools import get_assets_liabilities, exchange_rate, get_value, ytd_roi


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
            category=form.cleaned_data['category'],
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
                    value += obj.principal.amount / exchange_rate(obj.principal.currency)[0].amount
                else:
                    value += obj.principal.amount
            investments_summary.append({
                'holder': obj.holder,
                'value': Money(value, 'USD'),
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
        inv.rollover(
            form.cleaned_data['rate'],
            form.cleaned_data['start_date'],
            form.cleaned_data['duration'],
            form.cleaned_data['option'],
            form.cleaned_data['adjusted_amount'],
            form.cleaned_data['savings_account'],
        )
        return super().form_valid(form)


class InvestmentTerminationView(LoginRequiredMixin, FormView):
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
