from django.shortcuts import render
from django.views.generic.base import TemplateView

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
