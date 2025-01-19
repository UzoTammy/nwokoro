from django.contrib import admin
from .models import Saving, Investment, ExchangeRate

# Register your models here.
admin.site.register(Saving)
admin.site.register(Investment)
admin.site.register(ExchangeRate)

