from typing import Any

from django.views.generic.base import TemplateView

from .forms import NumberInputForm
from .tinyproject.numtoword import figure_word


# Create your views here.
class MainView(TemplateView):
    template_name = 'core/homepage.html'


class AboutMe(TemplateView):
    template_name = 'core/aboutme.html'


class ResumeView(TemplateView):
    template_name = 'core/resume.html'

class PortfolioRootView(TemplateView):
    template_name = 'core/portfolio/root.html'

class PortfolioScushView(TemplateView):
    template_name = 'core/portfolio/scushproject.html'


class PortfolioFinuelView(TemplateView):
    template_name = 'core/portfolio/finuel.html'
    

class TextingView(TemplateView):
    template_name = 'core/texting.html'


class NumberToWordView(TemplateView):
    template_name = 'core/portfolio/tinyprojects/numtoword.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        form = NumberInputForm()
        
        if 'submit' in self.request.GET:
            figure = self.request.GET['enter_number'].replace(',', '')
            context['figure'] = figure
            try:
                context['word'] = figure_word(figure)
            except OverflowError as err:
                context['word'] = f'{err}: only number less than or equal to 999 Trillion allowed'
            
        context['form'] = form
        return context