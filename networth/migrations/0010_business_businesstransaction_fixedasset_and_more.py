# Generated by Django 5.1.4 on 2025-01-27 23:06

import django.db.models.deletion
import django.utils.timezone
import djmoney.models.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('networth', '0009_financialdata'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Business',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('shares', models.PositiveIntegerField()),
                ('unit_cost_currency', djmoney.models.fields.CurrencyField(choices=[('CAD', 'Canadian Dollar'), ('NGN', 'Nigerian Naira'), ('USD', 'US Dollar')], default='CAD', editable=False, max_length=3)),
                ('unit_cost', djmoney.models.fields.MoneyField(decimal_places=2, max_digits=12)),
                ('host_country', models.CharField(max_length=2)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Business',
            },
        ),
        migrations.CreateModel(
            name='BusinessTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount_currency', djmoney.models.fields.CurrencyField(choices=[('CAD', 'Canadian Dollar'), ('NGN', 'Nigerian Naira'), ('USD', 'US Dollar')], default='CAD', editable=False, max_length=3)),
                ('amount', djmoney.models.fields.MoneyField(decimal_places=2, max_digits=12)),
                ('description', models.TextField(blank=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('transaction_type', models.CharField(max_length=2)),
                ('business', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='business_transactions', to='networth.business')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_business_transactions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='FixedAsset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('value_currency', djmoney.models.fields.CurrencyField(choices=[('CAD', 'Canadian Dollar'), ('NGN', 'Nigerian Naira'), ('USD', 'US Dollar')], default='CAD', editable=False, max_length=3)),
                ('value', djmoney.models.fields.MoneyField(decimal_places=2, max_digits=12)),
                ('host_country', models.CharField(max_length=2)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'FixedAsset',
            },
        ),
        migrations.CreateModel(
            name='FixedAssetTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount_currency', djmoney.models.fields.CurrencyField(choices=[('CAD', 'Canadian Dollar'), ('NGN', 'Nigerian Naira'), ('USD', 'US Dollar')], default='CAD', editable=False, max_length=3)),
                ('amount', djmoney.models.fields.MoneyField(decimal_places=2, max_digits=12)),
                ('description', models.TextField(blank=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('transaction_type', models.CharField(max_length=2)),
                ('fixed_asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fixed_asset_transactions', to='networth.fixedasset')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_fixed_asset_transactions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Liability',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('initial_amount_currency', djmoney.models.fields.CurrencyField(choices=[('CAD', 'Canadian Dollar'), ('NGN', 'Nigerian Naira'), ('USD', 'US Dollar')], default='CAD', editable=False, max_length=3)),
                ('initial_amount', djmoney.models.fields.MoneyField(decimal_places=2, max_digits=12)),
                ('balance_amount_currency', djmoney.models.fields.CurrencyField(choices=[('CAD', 'Canadian Dollar'), ('NGN', 'Nigerian Naira'), ('USD', 'US Dollar')], default='CAD', editable=False, max_length=3)),
                ('balance_amount', djmoney.models.fields.MoneyField(decimal_places=2, max_digits=12)),
                ('pay_method', models.CharField(max_length=30)),
                ('interest', models.DecimalField(decimal_places=2, max_digits=5)),
                ('host_country', models.CharField(max_length=2)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Liability',
            },
        ),
        migrations.CreateModel(
            name='LiabilityTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount_currency', djmoney.models.fields.CurrencyField(choices=[('CAD', 'Canadian Dollar'), ('NGN', 'Nigerian Naira'), ('USD', 'US Dollar')], default='CAD', editable=False, max_length=3)),
                ('amount', djmoney.models.fields.MoneyField(decimal_places=2, max_digits=12)),
                ('description', models.TextField(blank=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('transaction_type', models.CharField(max_length=2)),
                ('liability', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='liability_transactions', to='networth.liability')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_liability_transactions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
