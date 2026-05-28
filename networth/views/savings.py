from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models.aggregates import Max
from django.views.generic import TemplateView, CreateView, DetailView, UpdateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from djmoney.models.fields import Money

from ..forms import SavingForm, SavingFormUpdate, ConversionForm, SavingsCounterTransferForm
from ..models import Saving, FinancialData, SavingsTransaction
from ..tools import get_assets_liabilities, exchange_rate


class SavingListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'networth/saving_list.html'

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
        source: Saving = form.cleaned_data['source_account']
        receiver = form.cleaned_data['receiver_account']
        amount = form.cleaned_data['amount']
        converted_amount = form.cleaned_data['converted_amount']
        source.convert_fund(receiver, amount, converted_amount)
        messages.success(self.request, "Fund conversion complete !!!")
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
