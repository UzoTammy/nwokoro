
from django.urls import path
from .views import (NetworthHomeView, InvestmentCreateView, InvestmentUpdateView, SavingCreateView, SavingUpdateView)


urlpatterns = [
    path('', NetworthHomeView.as_view(), name='networth-home'),
    path('investment/create/', InvestmentCreateView.as_view(), name='networth-investment-create'),
    path('investment/<int:pk>/update/', InvestmentUpdateView.as_view(), name='networth-investment-update'),
    path('saving/create/', SavingCreateView.as_view(), name='networth-saving-create'),
    path('saving/<int:pk>/update/', SavingUpdateView.as_view(), name='networth-saving-update'),
]