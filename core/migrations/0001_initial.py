# Generated by Django 5.1.4 on 2025-01-03 15:56

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='StudentProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=30)),
                ('middle_name', models.CharField(blank=True, max_length=30, null=True)),
                ('last_name', models.CharField(max_length=30)),
                ('date_of_birth', models.DateField()),
                ('gender', models.CharField(max_length=7)),
                ('email', models.EmailField(max_length=254)),
                ('age', models.PositiveSmallIntegerField()),
                ('age_status', models.CharField(max_length=10)),
            ],
        ),
    ]
