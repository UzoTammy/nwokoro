from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('networth', '0012_fixedasset_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='fixedasset',
            name='growth_rate',
            field=models.FloatField(default=0),
        ),
    ]
