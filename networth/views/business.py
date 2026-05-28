from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.views.generic import TemplateView, DetailView, UpdateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from ..forms import BusinessCreateForm, BusinessUpdateForm, BusinessLiquidateForm, ReCapitalizeForm
from ..models import Saving, Business, FinancialData
from ..tools import get_assets_liabilities, get_value


class BusinessListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'networth/business_list.html'

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

        business = get_assets_liabilities(owner=self.request.user)['business']
        context['business'] = business.order_by('unit_cost_currency')
        context['business_total'] = get_value(business, 'business')
        context['to_usd_total'] = sum(biz.to_usd() for biz in business)
        return context


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
