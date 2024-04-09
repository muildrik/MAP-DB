# Generated by Django 3.2.9 on 2022-08-20 20:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('results', '0007_alter_collectionmodel_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collectionmodel',
            name='name',
            field=models.CharField(error_messages={'required': 'Your collection needs a unique name', 'unique': 'Your collection needs a unique name'}, max_length=60, unique=True),
        ),
    ]