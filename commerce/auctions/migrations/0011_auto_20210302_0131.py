# Generated by Django 3.1.7 on 2021-03-02 01:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0010_auto_20210226_2045'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listing',
            name='image',
            field=models.URLField(default='https://upload.wikimedia.org/wikipedia/commons/0/08/Image_tagging_icon_01.svg'),
        ),
    ]
