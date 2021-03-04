# Generated by Django 3.1.7 on 2021-03-02 01:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0011_auto_20210302_0131'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listing',
            name='category',
            field=models.ForeignKey(blank=True, default='3', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='listings', to='auctions.category'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='image',
            field=models.URLField(blank=True, default='https://upload.wikimedia.org/wikipedia/commons/5/53/Price_Tag_Flat_Icon_Vector.svg', null=True),
        ),
    ]