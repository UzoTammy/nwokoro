from django.urls import path
from .views import (MainView, ErrorView, AboutMe, ResumeView, PortfolioScushView, PortfolioFinuelView,
                     TextingView, NumberToWordView, TinyProjectView, DatabaseLearningView, PreferenceView,
                     AutomaticEmailView, NewHomeView, NewAboutMeView, ProfileView, StudentProfileView, 
                     StudentProfileUpdateView,PracticeView, TinyProjectTaxCanadaView, ActivateRegistrationView,
                     MeHome
                     )

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
    # path('portfolio/miniproject/database-learning/', DatabaseLearningView.as_view(), name='database-learning'),
    # path('portfolio/miniproject/auto-email/', AutomaticEmailView.as_view(), name='auto-email'),
    # path('portfolio/tinyproject/profile/', ProfileView.as_view(), name='tinyproject-profile'),
    # path('portfolio/miniproject/<str:filter_by>/', StudentProfileView.as_view(), name='profile-list'),
    # path('portfolio/miniproject/<int:pk>/update/', StudentProfileUpdateView.as_view(), name='profile-update'),
    # path('tinyproject/canada-tax', TinyProjectTaxCanadaView.as_view(), name='canada-tax-home'),
]

urlpatterns += [
    # path('tutorial/', PracticeView.as_view(), name='tutorials'),
]