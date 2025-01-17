
from django.urls import path
from .views import AchieveView, AchieveCreateView


urlpatterns = [
    path('', AchieveView.as_view(), name='achieve-home'),
    path('create/', AchieveCreateView.as_view(), name='achieve-create'),
    
]