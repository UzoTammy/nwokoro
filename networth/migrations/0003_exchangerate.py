# Generated by Django 5.1.4 on 2025-01-19 01:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('networth', '0002_investment_category_saving_category'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExchangeRate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('base_currency', models.CharField(max_length=3)),
                ('target_currency', models.CharField(max_length=3)),
                ('rate', models.FloatField()),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]