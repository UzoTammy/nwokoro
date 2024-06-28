from typing import Any
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from django.http import HttpRequest
from django.http.response import HttpResponse as HttpResponse
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
    template_name = 'core/portfolio/scush.html'


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
    
class DatabaseLearningView(TemplateView):
    template_name = 'core/portfolio/tinyprojects/databaselearning.html'

class AutomaticEmailView(TemplateView):
    template_name = 'core/portfolio/tinyprojects/auto_email.html'

class NewHomeView(TemplateView):
    template_name = 'core/home.html'

class NewAboutMeView(TemplateView):
    template_name = 'core/new_about_me.html'