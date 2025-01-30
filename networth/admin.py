from django.contrib import admin
from .models import (Saving, Investment, ExchangeRate, Stock, SavingsTransaction, Business,
                     InvestmentTransaction, StockTransaction, FinancialData, BusinessTransaction,
                     FixedAsset, FixedAssetTransaction)

# Register your models here.
admin.site.register(Saving)
admin.site.register(Investment)
admin.site.register(ExchangeRate)
admin.site.register(Stock)
admin.site.register(Business)
admin.site.register(FixedAsset)

admin.site.register(SavingsTransaction)
admin.site.register(InvestmentTransaction)
admin.site.register(StockTransaction)
admin.site.register(BusinessTransaction)
admin.site.register(FixedAssetTransaction)

admin.site.register(FinancialData)

