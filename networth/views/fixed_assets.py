from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.views.generic import TemplateView, DetailView, UpdateView, FormView, RedirectView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from ..forms import FixedAssetCreateForm, FixedAssetUpdateForm, FixedAssetRentForm, FixedAssetCollectRentForm
from ..models import Saving, FixedAsset, Rent, FinancialData
from ..tools import get_assets_liabilities, get_value


class FixedAssetListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'networth/fixed_asset_list.html'

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

        fixed_asset = get_assets_liabilities(owner=self.request.user)['fixed_asset']
        context['fixed_asset'] = fixed_asset.order_by('value_currency')
        context['fixed_asset_total'] = get_value(fixed_asset, 'asset')
        context['to_usd_total'] = sum(fa.to_usd() for fa in fixed_asset)
        return context


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
