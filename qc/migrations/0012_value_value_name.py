# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-07-30 09:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('qc', '0011_auto_20170730_1231'),
    ]

    operations = [
        migrations.AddField(
            model_name='value',
            name='value_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
