# Generated by Django 3.1.7 on 2021-03-03 23:16

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0022_auto_20210303_2303'),
    ]

    operations = [
        migrations.AddField(
            model_name='listing',
            name='wishlist_items',
            field=models.ManyToManyField(blank=True, related_name='wishlist_item', to=settings.AUTH_USER_MODEL),
        ),
    ]
