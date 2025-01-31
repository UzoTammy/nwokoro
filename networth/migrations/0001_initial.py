# Generated by Django 5.1.4 on 2025-01-18 17:41

import datetime
import django.db.models.deletion
import djmoney.models.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Investment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('holder', models.CharField(max_length=30)),
                ('principal_currency', djmoney.models.fields.CurrencyField(choices=[('CAD', 'Canadian Dollar'), ('NGN', 'Nigerian Naira'), ('USD', 'US Dollar')], default='CAD', editable=False, max_length=3)),
                ('principal', djmoney.models.fields.MoneyField(decimal_places=2, max_digits=10)),
                ('rate', models.FloatField()),
                ('start_date', models.DateField(default=datetime.date.today)),
                ('duration', models.PositiveSmallIntegerField()),
                ('host_country', models.CharField(max_length=30)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Saving',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('holder', models.CharField(max_length=30)),
                ('value_currency', djmoney.models.fields.CurrencyField(choices=[('CAD', 'Canadian Dollar'), ('NGN', 'Nigerian Naira'), ('USD', 'US Dollar')], default='CAD', editable=False, max_length=3)),
                ('value', djmoney.models.fields.MoneyField(decimal_places=2, max_digits=10)),
                ('host_country', models.CharField(max_length=30)),
                ('date', models.DateField(default=datetime.date.today)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
