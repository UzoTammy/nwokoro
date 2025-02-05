
from django.urls import path
from .views import (NetworthHomeView, DashboardView,
                    InvestmentCreateView, InvestmentDetailView, InvestmentRolloverView, InvestmentUpdateView, 
                    StockCreateView, StockDetailView, StockUpdateView,
                    SavingCreateView, SavingDetailView, SavingUpdateView,
                    BusinessCreateView, BusinessDetailView, BusinessUpdateView,
                    FixedAssetCreateView, FixedAssetDetailView, FixedAssetUpdateView,
                    ExternalFundHome, BorrowedFundView)


urlpatterns = [
    path('', NetworthHomeView.as_view(), name='networth-home'),
    path('dashboard/', DashboardView.as_view(), name='networth-dashboard'),
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

    path('business/<int:pk>/create/', BusinessCreateView.as_view(), name='networth-business-create'),
    path('business/<int:pk>/detail/', BusinessDetailView.as_view(), name='networth-business-detail'),
    path('business/<int:pk>/update/', BusinessUpdateView.as_view(), name='networth-business-update'),
    
    path('fixed-asset/<int:pk>/create/', FixedAssetCreateView.as_view(), name='networth-fixed-asset-create'),
    path('fixed-asset/<int:pk>/detail/', FixedAssetDetailView.as_view(), name='networth-fixed-asset-detail'),
    path('fixed-asset/<int:pk>/update/', FixedAssetUpdateView.as_view(), name='networth-fixed-asset-update'),

    path('external-fund/home/', ExternalFundHome.as_view(), name='networth-external-fund-home'),
    path('<int:pk>/borrow-fund/', BorrowedFundView.as_view(), name='networth-borrow-fund'),
    
    
]