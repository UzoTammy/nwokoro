from django.http import Http404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

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
        context['next_tutorial'] = (
            INVESTMENT_TUTORIALS[index + 1] if index < len(INVESTMENT_TUTORIALS) - 1 else None
        )
        return context
