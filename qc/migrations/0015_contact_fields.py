# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-08-05 13:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('qc', '0014_auto_20170805_1545'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='fields',
            field=models.TextField(blank=True, null=True),
        ),
    ]
