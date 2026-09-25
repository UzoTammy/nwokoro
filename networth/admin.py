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



from .models import CountryRisk, CurrencyRisk, InstitutionRisk, AssetTypeRisk


@admin.register(CountryRisk)
class CountryRiskAdmin(admin.ModelAdmin):
    list_display = ('code', 'sovereign', 'convertibility', 'at_war', 'reviewed_on', 'source')
    list_editable = ('sovereign', 'convertibility', 'at_war', 'reviewed_on')


@admin.register(CurrencyRisk)
class CurrencyRiskAdmin(admin.ModelAdmin):
    list_display = ('currency', 'stress_floor', 'reviewed_on', 'source')
    list_editable = ('stress_floor', 'reviewed_on')


@admin.register(InstitutionRisk)
class InstitutionRiskAdmin(admin.ModelAdmin):
    list_display = ('name', 'aliases', 'failure_probability', 'loss_given_failure', 'insured_limit', 'reviewed_on')
    list_editable = ('failure_probability', 'loss_given_failure', 'reviewed_on')


@admin.register(AssetTypeRisk)
class AssetTypeRiskAdmin(admin.ModelAdmin):
    list_display = ('asset_class', 'category', 'stress', 'reviewed_on', 'source')
    list_editable = ('stress', 'reviewed_on')
