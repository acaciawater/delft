# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2021-01-20 23:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('data', '0040_auto_20190811_1156'),
    ]

    operations = [
        migrations.CreateModel(
            name='Alarm',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('options', models.TextField(blank=True, null=True, verbose_name='options')),
                ('sent', models.DateTimeField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.DateTimeField()),
                ('message', models.TextField(blank=True, null=True)),
                ('alarm', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='delft.Alarm')),
            ],
        ),
        migrations.CreateModel(
            name='Inspector',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='naam')),
                ('classname', models.CharField(help_text='volledige naam van de inspector klasse, bijvoorbeeld delft.models.Changed', max_length=50, verbose_name='python klasse')),
                ('description', models.TextField(blank=True, null=True, verbose_name='omschrijving')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Receiver',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
            ],
        ),
        migrations.AddField(
            model_name='alarm',
            name='inspector',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='delft.Inspector'),
        ),
        migrations.AddField(
            model_name='alarm',
            name='receivers',
            field=models.ManyToManyField(to='delft.Receiver'),
        ),
        migrations.AddField(
            model_name='alarm',
            name='series',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.Series'),
        ),
    ]
