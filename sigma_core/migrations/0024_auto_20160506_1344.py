# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-05-06 11:44
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sigma_core', '0023_auto_20160215_1346'),
    ]

    operations = [
        migrations.RenameField(
            model_name='group',
            old_name='private',
            new_name='is_private',
        ),
        migrations.RenameField(
            model_name='group',
            old_name='protected',
            new_name='is_protected',
        ),
    ]
