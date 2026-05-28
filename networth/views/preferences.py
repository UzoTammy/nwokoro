from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from account.models import Preference
from ..forms import NetworthPreferenceForm


class NetworthPreferenceView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """User-editable defaults for forecast rates, period, and email notifications."""
    template_name = 'networth/preference.html'
    form_class    = NetworthPreferenceForm
    success_url   = reverse_lazy('networth-preference')

    def test_func(self):
        return self.request.user.is_staff

    def get_object(self, queryset=None):
        pref, _ = Preference.objects.get_or_create(user=self.request.user)
        return pref

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pref'] = self.get_object()
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Preferences saved.')
        return super().form_valid(form)
