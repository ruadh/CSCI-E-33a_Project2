# Generated by Django 3.1.7 on 2021-03-02 18:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0018_auto_20210302_1810'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='body',
            field=models.TextField(max_length=300),
        ),
    ]
