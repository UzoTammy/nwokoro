# Generated by Django 5.1.4 on 2025-01-27 09:33

import djmoney.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('networth', '0008_stock_stocktransaction'),
    ]

    operations = [
        migrations.CreateModel(
            name='FinancialData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('worth_currency', djmoney.models.fields.CurrencyField(choices=[('CAD', 'Canadian Dollar'), ('NGN', 'Nigerian Naira'), ('USD', 'US Dollar')], default='CAD', editable=False, max_length=3)),
                ('worth', djmoney.models.fields.MoneyField(decimal_places=2, max_digits=12)),
                ('savings_currency', djmoney.models.fields.CurrencyField(choices=[('CAD', 'Canadian Dollar'), ('NGN', 'Nigerian Naira'), ('USD', 'US Dollar')], default='CAD', editable=False, max_length=3)),
                ('savings', djmoney.models.fields.MoneyField(decimal_places=2, max_digits=12)),
                ('investment_currency', djmoney.models.fields.CurrencyField(choices=[('CAD', 'Canadian Dollar'), ('NGN', 'Nigerian Naira'), ('USD', 'US Dollar')], default='CAD', editable=False, max_length=3)),
                ('investment', djmoney.models.fields.MoneyField(decimal_places=2, max_digits=12)),
                ('stock_currency', djmoney.models.fields.CurrencyField(choices=[('CAD', 'Canadian Dollar'), ('NGN', 'Nigerian Naira'), ('USD', 'US Dollar')], default='CAD', editable=False, max_length=3)),
                ('stock', djmoney.models.fields.MoneyField(decimal_places=2, max_digits=12)),
                ('business_currency', djmoney.models.fields.CurrencyField(choices=[('CAD', 'Canadian Dollar'), ('NGN', 'Nigerian Naira'), ('USD', 'US Dollar')], default='CAD', editable=False, max_length=3)),
                ('business', djmoney.models.fields.MoneyField(decimal_places=2, max_digits=12)),
                ('fixed_asset_currency', djmoney.models.fields.CurrencyField(choices=[('CAD', 'Canadian Dollar'), ('NGN', 'Nigerian Naira'), ('USD', 'US Dollar')], default='CAD', editable=False, max_length=3)),
                ('fixed_asset', djmoney.models.fields.MoneyField(decimal_places=2, max_digits=12)),
                ('liability_currency', djmoney.models.fields.CurrencyField(choices=[('CAD', 'Canadian Dollar'), ('NGN', 'Nigerian Naira'), ('USD', 'US Dollar')], default='CAD', editable=False, max_length=3)),
                ('liability', djmoney.models.fields.MoneyField(decimal_places=2, max_digits=12)),
                ('roi_currency', djmoney.models.fields.CurrencyField(choices=[('CAD', 'Canadian Dollar'), ('NGN', 'Nigerian Naira'), ('USD', 'US Dollar')], default='CAD', editable=False, max_length=3)),
                ('roi', djmoney.models.fields.MoneyField(decimal_places=2, max_digits=12)),
                ('daily_roi_currency', djmoney.models.fields.CurrencyField(choices=[('CAD', 'Canadian Dollar'), ('NGN', 'Nigerian Naira'), ('USD', 'US Dollar')], default='CAD', editable=False, max_length=3)),
                ('daily_roi', djmoney.models.fields.MoneyField(decimal_places=2, max_digits=12)),
                ('present_roi_currency', djmoney.models.fields.CurrencyField(choices=[('CAD', 'Canadian Dollar'), ('NGN', 'Nigerian Naira'), ('USD', 'US Dollar')], default='CAD', editable=False, max_length=3)),
                ('present_roi', djmoney.models.fields.MoneyField(decimal_places=2, max_digits=12)),
            ],
        ),
    ]
