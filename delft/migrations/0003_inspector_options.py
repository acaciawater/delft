# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2021-01-20 23:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('delft', '0002_receiver_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='inspector',
            name='options',
            field=models.TextField(blank=True, null=True, verbose_name='default options'),
        ),
    ]
