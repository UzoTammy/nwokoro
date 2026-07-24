import datetime

from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.views.generic import ListView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin

from djmoney.models.fields import Money

from ..forms import BorrowedFundForm, RewardFundForm, InjectFundForm
from ..models import Saving, RewardFund, InjectFund, BorrowedFund, FinancialData
from ..tools import exchange_rate


class RewardFundListView(LoginRequiredMixin, ListView):
    model = RewardFund
    template_name = 'networth/reward_list.html'
    context_object_name = 'rewards'

    def get_queryset(self):
        return RewardFund.objects.filter(owner=self.request.user).order_by('-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rewards = context['rewards']

        def _to_usd_amount(reward):
            if reward.amount.currency != 'USD':
                return reward.amount.amount / exchange_rate(reward.amount.currency)[0].amount
            return reward.amount.amount

        context['to_usd_total'] = Money(sum(_to_usd_amount(r) for r in rewards), 'USD')

        current_year = datetime.date.today().year
        ytd_rewards = rewards.filter(date__year=current_year)
        context['ytd_usd_total'] = Money(sum(_to_usd_amount(r) for r in ytd_rewards), 'USD')

        fd_this_year = FinancialData.objects.filter(
            owner=self.request.user, date__year=current_year
        ).order_by('date')
        growth_usd = 0
        if fd_this_year.exists():
            growth = fd_this_year.last().worth - fd_this_year.first().worth
            if growth.currency != 'USD':
                growth_usd = growth.amount / exchange_rate(growth.currency)[0].amount
            else:
                growth_usd = growth.amount
        context['networth_growth_usd'] = Money(growth_usd, 'USD')
        context['reward_growth_chart'] = {
            'labels': ['Reward Taken', 'Networth Growth'],
            'values': [float(context['ytd_usd_total'].amount), float(max(growth_usd, 0))],
        }
        return context


class ExternalFundHome(LoginRequiredMixin, ListView):
    model = Saving
    template_name = 'networth/external_fund.html'

    def post(self, request, *args, **kwargs):
        if not ('radioAction' in request.POST and 'radioSaving' in request.POST):
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
        savings_account.borrow(
            form.cleaned_data['source'],
            form.cleaned_data['borrowed_amount'],
            form.cleaned_data['settlement_amount'],
            form.cleaned_data['date'],
            form.cleaned_data['terminal_date'],
            form.cleaned_data['description'],
        )
        messages.success(self.request, 'Transaction is successful !!!')
        return super().form_valid(form)
