
from django.urls import path
from .views import (ChoreHome, RegistrationMessage, ChoreDashboard, ChoreSetupView, WorkCreateView, WorkEvaluateView, BonusPointCreateView, 
                    BonusUpdateView, WorkDoneView, WorkDetailView, JobRegisterCreateView,
                    WorkListView, AssignWorkView, JobRegisterListView, DelegateWorkCreateView,
                    InitiateWorkCreateView, InitiateWorkDetailView, InitiateWorkApproveView,ChoreExtendTime,
                    JobRegisterUpdateView, ConcludedWorkListView, ConcludedWorDetailView, CompletedJobDecisionView,
                    DecisionView)
from django.views.generic import TemplateView

urlpatterns = [
    path('', ChoreHome.as_view(), name='chore-home'),
    path('registration-message/', RegistrationMessage.as_view(), name='chore-registration-message'),
    path('dashboard/', ChoreDashboard.as_view(), name='chore-dashboard'),
    path('setup/', ChoreSetupView.as_view(), name='chore-setup'),
    path('work/create/', WorkCreateView.as_view(), name='work-create'),
    path('work-evaluate/', WorkEvaluateView.as_view(), name='work-evaluate'),
    path('bonus-point-new/', BonusPointCreateView.as_view(),name='chore-bonus-point-new'),
    path('<int:pk>/bonus/', BonusUpdateView.as_view(), name='bonus-update'),
    path('<int:pk>/work-done/', WorkDoneView.as_view(), name='work-done'),
    path('work/list/', WorkListView.as_view(), name='work-list'),
    path('work/<int:pk>/', WorkDetailView.as_view(), name='work-detail'),
    path('assign-work/', AssignWorkView.as_view(), name='assign-work-list'),
    path('job-register/list/', JobRegisterListView.as_view(), name='job-register-list'),
    path('job-register/create/', JobRegisterCreateView.as_view(), name='job-register-create'),
    path('job-register/update/<int:pk>/', JobRegisterUpdateView.as_view(), name='job-register-update'),
    path('help/', TemplateView.as_view(template_name='chore/helper.html'), name='chore-help'),
    path('delegate/', DelegateWorkCreateView.as_view(), name='delegate-work'),
    path('initiate/', InitiateWorkCreateView.as_view(), name='initiate-work'),
    path('<int:pk>/initiate-detail/', InitiateWorkDetailView.as_view(), name='initiate-work-detail'),
    path('<int:pk>/initiate-approve/', InitiateWorkApproveView.as_view(), name='initiate-work-approve'),
    path('concluded/', ConcludedWorkListView.as_view(), name='concluded-job'),
    path('concluded/<int:pk>/detail/', ConcludedWorDetailView.as_view(), name='concluded-detail'),
    path('<int:pk>/completed-job/', CompletedJobDecisionView.as_view(), name='completed-job-decision'),
    path('decision/<int:pk>/', DecisionView.as_view(), name='decided'),
    path('extend-time/<int:pk>/', ChoreExtendTime.as_view(), name='extend-time')
]