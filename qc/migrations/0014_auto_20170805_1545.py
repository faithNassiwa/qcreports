# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-08-05 12:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('qc', '0013_auto_20170805_1152'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contact',
            old_name='fields',
            new_name='number_of_weeks',
        ),
        migrations.AddField(
            model_name='contact',
            name='points',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]