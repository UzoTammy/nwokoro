# Generated by Django 5.1.4 on 2025-03-20 20:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('networth', '0003_alter_business_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='business',
            name='description',
            field=models.CharField(default='', max_length=250),
        ),
        migrations.AddField(
            model_name='fixedasset',
            name='description',
            field=models.CharField(default='', max_length=250),
        ),
        migrations.AddField(
            model_name='investment',
            name='description',
            field=models.CharField(default='', max_length=250),
        ),
        migrations.AddField(
            model_name='saving',
            name='description',
            field=models.CharField(default='', max_length=250),
        ),
        migrations.AddField(
            model_name='stock',
            name='description',
            field=models.CharField(default='', max_length=250),
        ),
    ]
