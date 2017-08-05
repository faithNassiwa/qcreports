# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-08-05 08:52
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('qc', '0012_value_value_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='flow',
            name='sync_flows',
        ),
        migrations.AlterField(
            model_name='run',
            name='flow',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='qc.Flow'),
        ),
    ]
