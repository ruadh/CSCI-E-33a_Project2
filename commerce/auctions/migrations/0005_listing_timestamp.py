# Generated by Django 3.1.7 on 2021-02-26 01:39

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0004_auto_20210226_0120'),
    ]

    operations = [
        migrations.AddField(
            model_name='listing',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
