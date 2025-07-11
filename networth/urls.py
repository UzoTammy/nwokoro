
from django.urls import path
from .views import (NetworthHomeView, DashboardView,
                    InvestmentCreateView, InvestmentDetailView,
                    InvestmentRolloverView, InvestmentUpdateView,
                    InvestmentTerminationView,
                    StockCreateView, StockDetailView, StockUpdateView,
                    SavingCreateView, SavingDetailView, SavingUpdateView,
                    SavingsConversionView,
                    BusinessCreateView, BusinessDetailView, BusinessUpdateView, BusinessPlowBackView,
                    BusinessLiquidateView,
                    FixedAssetCreateView, FixedAssetDetailView, FixedAssetUpdateView,FixedAssetRentView,
                    FixedAssetCollectRentView, FixedAssetStopRentView, FixedAssetRestoreRentView,
                    FixedAssetUpdateRentView,
                    ExternalFundHome, RewardFundView, InjectFundView, BorrowedFundView, SavingsCounterTransferView, InstitutionReportView,
                    PDFNetworthReport, LiabilityDetailView, LiabilityUpdateView, LiabilityRepayView)


urlpatterns = [
    path('', NetworthHomeView.as_view(), name='networth-home'),
    path('dashboard/', DashboardView.as_view(), name='networth-dashboard'),
    path('investment/<int:pk>/create/', InvestmentCreateView.as_view(),
         name='networth-investment-create'),
    path('investment/<int:pk>/detail/', InvestmentDetailView.as_view(),
         name='networth-investment-detail'),
    path('investment/<int:pk>/update/', InvestmentUpdateView.as_view(),
         name='networth-investment-update'),
    path('investment/<int:pk>/rollover/', InvestmentRolloverView.as_view(),
         name='networth-investment-rollover'),
    path('investment/<int:pk>/terminate/', InvestmentTerminationView.as_view(),
         name='networth-investment-terminate'),

    path('stock/<int:pk>/create/', StockCreateView.as_view(),
         name='networth-stock-create'),
    path('stock/<int:pk>/detail/', StockDetailView.as_view(),
         name='networth-stock-detail'),
    path('stock/<int:pk>/update/', StockUpdateView.as_view(),
         name='networth-stock-update'),

    path('saving/create/', SavingCreateView.as_view(),
         name='networth-saving-create'),
    path('saving/<int:pk>/detail/', SavingDetailView.as_view(),
         name='networth-saving-detail'),
    path('saving/<int:pk>/update/', SavingUpdateView.as_view(),
         name='networth-saving-update'),
    path('saving/conversion/', SavingsConversionView.as_view(),
         name='saving-conversion'),

    path('business/<int:pk>/create/', BusinessCreateView.as_view(),
         name='networth-business-create'),
    path('business/<int:pk>/detail/', BusinessDetailView.as_view(),
         name='networth-business-detail'),
    path('business/<int:pk>/update/', BusinessUpdateView.as_view(),
         name='networth-business-update'),
     path('business/<int:pk>/plow_back/', BusinessPlowBackView.as_view(),
         name='networth-business-plow-back'),
     path('business/<int:pk>/liquate/', BusinessLiquidateView.as_view(),
         name='networth-business-liquidate'),
     
    path('fixed-asset/<int:pk>/create/', FixedAssetCreateView.as_view(),
         name='networth-fixed-asset-create'),
    path('fixed-asset/<int:pk>/detail/', FixedAssetDetailView.as_view(),
         name='networth-fixed-asset-detail'),
    path('fixed-asset/<int:pk>/update/', FixedAssetUpdateView.as_view(),
         name='networth-fixed-asset-update'),
     path('fixed-asset/<int:pk>/rent/', FixedAssetRentView.as_view(),
         name='networth-fixed-asset-rent'),
     path('fixed-asset/<int:pk>/rent/collect/', FixedAssetCollectRentView.as_view(),
         name='networth-fixed-asset-rent-collect'),
     path('fixed-asset/<int:pk>/rent/stop/', FixedAssetStopRentView.as_view(),
         name='networth-fixed-asset-rent-stop'),
     path('fixed-asset/<int:pk>/rent/restore/', FixedAssetRestoreRentView.as_view(),
         name='networth-fixed-asset-rent-restore'),
     path('fixed-asset/<int:pk>/rent/<int:rent_pk>/update/', FixedAssetUpdateRentView.as_view(),
         name='networth-fixed-asset-rent-update'),

     #liability
    path('liability/<int:pk>/detail/', LiabilityDetailView.as_view(),
         name='networth-liability-detail'),
    path('liability/<int:pk>/update/', LiabilityUpdateView.as_view(),
         name='networth-liability-update'),
     path('liability/<int:pk>/repay/', LiabilityRepayView.as_view(),
         name='networth-liability-repay'),


    path('external-fund/home/', ExternalFundHome.as_view(),
         name='networth-external-fund-home'),

    path('<int:pk>/reward-fund/', RewardFundView.as_view(),
         name='networth-reward-fund'),

    path('<int:pk>/inject-fund/', InjectFundView.as_view(),
         name='networth-inject-fund'),

    path('<int:pk>/borrow-fund/', BorrowedFundView.as_view(),
         name='networth-borrow-fund'),

    path('saving/counter-transfer/', SavingsCounterTransferView.as_view(),
         name='saving-counter-transfer'),

    path('institution-report', InstitutionReportView.as_view(),
         name='institution-report'),

    path('pdf/networth', PDFNetworthReport.as_view(), name='pdf-networth')
]
