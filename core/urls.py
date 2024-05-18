from django.urls import path
from .views import (MainView, AboutMe, ResumeView, PortfolioScushView, PortfolioFinuelView,
                     TextingView, NumberToWordView, PortfolioRootView, DatabaseLearningView)

urlpatterns = [
    path('', MainView.as_view(), name='index'),
    path('aboutme/', AboutMe.as_view(), name='about-me'),
    path('resume-view/', ResumeView.as_view(), name='resume'),
    path('portfolio-scush/', PortfolioScushView.as_view(), name='portfolio-scush'),
    path('portfolio-finuel/', PortfolioFinuelView.as_view(), name='portfolio-finuel'),
    path('texting-it/', TextingView.as_view(), name='texting-it'),

    
]

urlpatterns += [
    path('portfolio-root/', PortfolioRootView.as_view(), name='portfolio-root'),
    path('portfolio/miniproject/number-to-word/', NumberToWordView.as_view(), name='number-to-word'),
    path('portfolio/miniproject/database-learning/', DatabaseLearningView.as_view(), name='database-learning'),
    
    
]