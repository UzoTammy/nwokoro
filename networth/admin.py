from django.contrib import admin
from .models import Saving, Investment, ExchangeRate, Stock, SavingsTransaction, InvestmentTransaction, StockTransaction, FinancialData

# Register your models here.
admin.site.register(Saving)
admin.site.register(Investment)
admin.site.register(ExchangeRate)
admin.site.register(Stock)

admin.site.register(SavingsTransaction)
admin.site.register(InvestmentTransaction)
admin.site.register(StockTransaction)

admin.site.register(FinancialData)

