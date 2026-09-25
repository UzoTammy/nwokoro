from django.http import Http404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from ..risk import portfolio_risk
from ..tutorials import INVESTMENT_TUTORIALS, get_tutorial


class TutorialListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'networth/tutorial_list.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tutorials'] = INVESTMENT_TUTORIALS
        return context


class TutorialDetailView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'networth/tutorial_detail.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tutorial = get_tutorial(self.kwargs['slug'])
        if tutorial is None:
            raise Http404('Tutorial not found')
        context['tutorial'] = tutorial

        index = INVESTMENT_TUTORIALS.index(tutorial)
        context['prev_tutorial'] = INVESTMENT_TUTORIALS[index - 1] if index > 0 else None
        return context


class TutorialGrowthView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'networth/tutorial_growth.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tutorial = get_tutorial(self.kwargs['slug'])
        if tutorial is None:
            raise Http404('Tutorial not found')
        context['tutorial'] = tutorial

        index = INVESTMENT_TUTORIALS.index(tutorial)
        context['next_tutorial'] = (
            INVESTMENT_TUTORIALS[index + 1] if index < len(INVESTMENT_TUTORIALS) - 1 else None
        )
        return context


class RiskScoreStudyView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'networth/risk_score_study.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        risk = portfolio_risk(self.request.user)
        if risk.get('available'):
            risk['assets'] = sorted(risk['assets'], key=lambda a: a.value_usd * a.risk, reverse=True)
        context['portfolio_risk'] = risk
        return context
