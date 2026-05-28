from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.views.generic import TemplateView, DetailView, UpdateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from ..forms import BorrowedFundForm, LiabilityRepayForm
from ..models import BorrowedFund, FinancialData
from ..tools import get_assets_liabilities, get_value


class LiabilityListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'networth/liability_list.html'

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

        liabilities = get_assets_liabilities(owner=self.request.user)['liabilities']
        context['liabilities'] = liabilities.order_by('host_country')
        context['liabilities_total'] = get_value(liabilities, 'liability')
        context['to_usd_total'] = sum(liability.to_usd() for liability in liabilities)
        return context


class LiabilityDetailView(LoginRequiredMixin, DetailView):
    model = BorrowedFund
    template_name = 'networth/liability_detail.html'


class LiabilityUpdateView(LoginRequiredMixin, UpdateView):
    model = BorrowedFund
    template_name = 'networth/borrow_form.html'
    form_class = BorrowedFundForm

    def get_success_url(self):
        return reverse('networth-liability-detail', kwargs={'pk': self.kwargs['pk']})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        borrowedfund = BorrowedFund.objects.get(pk=self.kwargs.get('pk'))
        kwargs['pk'] = borrowedfund.savings_account.pk
        return kwargs


class LiabilityRepayView(LoginRequiredMixin, FormView):
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
            form.cleaned_data['savings_account'],
        )
        messages.success(self.request, f"Repayment made from {form.cleaned_data['savings_account']}")
        return super().form_valid(form)
