# Generated by Django 3.2.9 on 2022-08-20 19:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('results', '0002_collectionmodel_uploaddatafilemodel'),
    ]

    operations = [
        migrations.CreateModel(
            name='CollectionField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60)),
                ('type', models.CharField(choices=[('T', 'Text'), ('N', 'Number'), ('B', 'Boolean'), ('D', 'Date')], default='T', max_length=2)),
                ('max_length', models.IntegerField(default=0)),
                ('required', models.BooleanField(default=False)),
                ('index', models.BooleanField(default=True)),
                ('autotrans_key', models.BooleanField(default=True)),
                ('autotrans_val', models.BooleanField(default=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='collectionmodel',
            name='schema',
        ),
        migrations.AddField(
            model_name='collectionmodel',
            name='schema',
            field=models.ManyToManyField(to='results.CollectionField'),
        ),
    ]
