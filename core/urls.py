from django.urls import path
from .views import (MainView, ErrorView, AboutMe, ResumeView, PortfolioScushView, PortfolioFinuelView,
                     TextingView, NumberToWordView, TinyProjectView, PreferenceView, NewHomeView, NewAboutMeView,
                    ActivateRegistrationView, MeHome)

urlpatterns = [
    path('', MainView.as_view(), name='index'),
    path('preference/', PreferenceView.as_view(), name='preference'),
    path('activate-registration', ActivateRegistrationView.as_view(), name='activate-registration'),
    path('oops/', ErrorView.as_view(), name='error-message'),
    path('aboutme/', AboutMe.as_view(), name='about-me'),
    path('me/home', MeHome.as_view(), name='me-home'),
    path('new-about-me', NewAboutMeView.as_view(), name='new-aboutme'),
    path('resume-view/', ResumeView.as_view(), name='resume'),
    path('portfolio-scush/', PortfolioScushView.as_view(), name='portfolio-scush'),
    path('portfolio-finuel/', PortfolioFinuelView.as_view(), name='portfolio-finuel'),
    path('texting-it/', TextingView.as_view(), name='texting-it'),
    path('new-home/', NewHomeView.as_view(), name='new-home')
    
]

urlpatterns += [
    path('tinyproject/', TinyProjectView.as_view(), name='tinyproject-home'),
    path('portfolio/miniproject/number-to-word/', NumberToWordView.as_view(), name='number-to-word'),
]
