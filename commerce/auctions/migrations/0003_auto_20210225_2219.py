# Generated by Django 3.1.7 on 2021-02-25 22:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0002_bid_category_comment_listing_wishlistitem'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=64, unique=True),
        ),
    ]