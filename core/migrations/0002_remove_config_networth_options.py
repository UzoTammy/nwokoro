# Generated by Django 5.1.4 on 2025-03-20 06:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='config',
            name='networth_options',
        ),
    ]
