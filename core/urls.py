from django.urls import path
from .views import MainView, AboutMe, ResumeView, PortfolioScushView, PortfolioFinuelView, TextingView

urlpatterns = [
    path('', MainView.as_view(), name='index'),
    path('aboutme/', AboutMe.as_view(), name='about-me'),
    path('resume-view/', ResumeView.as_view(), name='resume'),
    path('portfolio/scush', PortfolioScushView.as_view(), name='portfolio-scush'),
    path('portfolio-finuel/', PortfolioFinuelView.as_view(), name='portfolio-finuel'),
    path('texting-it', TextingView.as_view(), name='texting-it'),
    
]