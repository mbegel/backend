# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-02-01 10:09
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sigma_core', '0014_auto_20160201_1109'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='groupacknowledgment',
            name='asking_group',
        ),
        migrations.RemoveField(
            model_name='groupacknowledgment',
            name='validator_group',
        ),
    ]