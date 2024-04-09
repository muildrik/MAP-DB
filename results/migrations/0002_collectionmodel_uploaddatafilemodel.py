# Generated by Django 3.2.9 on 2022-08-20 18:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('results', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CollectionModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60)),
                ('schema', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='UploadDataFileModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60)),
                ('file', models.FileField(blank=True, null=True, upload_to='media')),
                ('collection', models.OneToOneField(default='data', on_delete=django.db.models.deletion.CASCADE, to='results.collectionmodel')),
            ],
        ),
    ]