from typing import Any
from django.shortcuts import render
from django.views.generic.base import TemplateView
from .forms import NumberForm
from .tinyproject.numtoword import figure_word

# Create your views here.
class MainView(TemplateView):
    template_name = 'core/homepage.html'


class AboutMe(TemplateView):
    template_name = 'core/aboutme.html'


class ResumeView(TemplateView):
    template_name = 'core/resume.html'


class PortfolioScushView(TemplateView):
    template_name = 'core/portfolio/scushproject.html'

class PortfolioFinuelView(TemplateView):
    template_name = 'core/portfolio/finuel.html'
    
class TextingView(TemplateView):
    template_name = 'core/texting.html'

class NumberToWordView(TemplateView):
    template_name = 'core/portfolio/miniprojects/numtoword.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['form'] = NumberForm()
        if 'submit' in self.request.GET:
            figure = self.request.GET['figure']
            context['figure'] = figure
            context['word'] = figure_word(figure)
        
        return context
    
    