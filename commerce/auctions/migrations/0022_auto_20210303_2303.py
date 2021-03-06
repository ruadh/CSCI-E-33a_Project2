# Generated by Django 3.1.7 on 2021-03-03 23:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0021_auto_20210302_2152'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bid',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=9, verbose_name='Your Bid'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='body',
            field=models.TextField(max_length=500),
        ),
        migrations.DeleteModel(
            name='WatchlistItem',
        ),
    ]
