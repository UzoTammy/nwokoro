# Generated by Django 5.1.4 on 2025-02-02 07:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('networth', '0011_borrowedfund_borrowedfundtransaction'),
    ]

    operations = [
        migrations.AddField(
            model_name='financialdata',
            name='networth_by_country',
            field=models.JSONField(null=True),
        ),
    ]
