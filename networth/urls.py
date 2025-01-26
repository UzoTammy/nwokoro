
from django.urls import path
from .views import (NetworthHomeView, 
                    InvestmentCreateView, InvestmentDetailView, InvestmentRolloverView, InvestmentUpdateView, 
                    StockCreateView, StockDetailView, StockUpdateView,
                    SavingCreateView, SavingDetailView, SavingUpdateView)


urlpatterns = [
    path('', NetworthHomeView.as_view(), name='networth-home'),
    path('investment/<int:pk>/create/', InvestmentCreateView.as_view(), name='networth-investment-create'),
    path('investment/<int:pk>/detail/', InvestmentDetailView.as_view(), name='networth-investment-detail'),
    path('investment/<int:pk>/update/', InvestmentUpdateView.as_view(), name='networth-investment-update'),
    path('investment/<int:pk>/rollover/', InvestmentRolloverView.as_view(), name='networth-investment-rollover'),
    
    path('stock/<int:pk>/create/', StockCreateView.as_view(), name='networth-stock-create'),
    path('stock/<int:pk>/detail/', StockDetailView.as_view(), name='networth-stock-detail'),
    path('stock/<int:pk>/update/', StockUpdateView.as_view(), name='networth-stock-update'),
    
    path('saving/create/', SavingCreateView.as_view(), name='networth-saving-create'),
    path('saving/<int:pk>/detail/', SavingDetailView.as_view(), name='networth-saving-detail'),
    path('saving/<int:pk>/update/', SavingUpdateView.as_view(), name='networth-saving-update'),
]