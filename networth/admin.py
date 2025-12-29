from django.contrib import admin
from .models import (Saving, Investment, ExchangeRate, Stock, SavingsTransaction, Business,
                     InvestmentTransaction, StockTransaction, FinancialData, BusinessTransaction,
                     FixedAsset, FixedAssetTransaction, RewardFund, InjectFund,
                     BorrowedFund, BorrowedFundTransaction, Rent, Liability, LiabilityTransaction)

# Register your models here.
admin.site.register(Saving)
admin.site.register(Investment)
admin.site.register(ExchangeRate)
admin.site.register(Stock)
admin.site.register(Business)
admin.site.register(FixedAsset)
admin.site.register(BorrowedFund)
admin.site.register(RewardFund)
admin.site.register(InjectFund)
admin.site.register(Liability)

admin.site.register(Rent)

admin.site.register(SavingsTransaction)
admin.site.register(InvestmentTransaction)
admin.site.register(StockTransaction)
admin.site.register(BusinessTransaction)
admin.site.register(FixedAssetTransaction)
admin.site.register(BorrowedFundTransaction)
admin.site.register(LiabilityTransaction)

admin.site.register(FinancialData)

