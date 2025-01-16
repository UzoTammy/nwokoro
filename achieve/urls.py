
from django.urls import path
from .views import AchieveView


urlpatterns = [
    path('', AchieveView.as_view(), name='achieve-home'),
]