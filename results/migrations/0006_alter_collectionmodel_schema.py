# Generated by Django 3.2.9 on 2022-08-20 20:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('results', '0005_alter_collectionfield_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collectionmodel',
            name='schema',
            field=models.ManyToManyField(blank=True, null=True, to='results.CollectionField'),
        ),
    ]