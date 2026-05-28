from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import TemplateView, DetailView, UpdateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from ..forms import StockCreateForm, StockUpdateForm
from ..models import Saving, Stock, FinancialData
from ..tools import get_assets_liabilities, get_value


class StockListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'networth/stock_list.html'

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

        stocks = get_assets_liabilities(owner=self.request.user)['stocks']
        context['stocks'] = stocks.order_by('unit_cost_currency')
        context['stock_total'] = get_value(stocks, 'stock')
        context['to_usd_total'] = sum(stock.to_usd() for stock in stocks)
        return context


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
        savings_account = Saving.objects.get(pk=self.kwargs['pk'])
        savings_account.create_stock(
            holder=form.cleaned_data['holder'],
            units=form.cleaned_data['units'],
            unit_cost=form.cleaned_data['unit_cost'],
            unit_price=form.cleaned_data['unit_cost'],
            date_bought=form.cleaned_data['date_bought'],
            stock_type=form.cleaned_data['stock_type'],
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
