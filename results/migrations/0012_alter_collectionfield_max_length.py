# Generated by Django 3.2.9 on 2022-08-20 21:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('results', '0011_auto_20220820_1711'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collectionfield',
            name='max_length',
            field=models.IntegerField(blank=True, default='', error_messages={'data_type': 'Please provide a numeric value only'}, null=True),
        ),
    ]