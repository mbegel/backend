# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-02-01 17:12
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sigma_files', '0002_auto_20160201_1812'),
        ('sigma_core', '0016_group_field_group__member_value__validator'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='photo',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='sigma_files.ProfileImage'),
        ),
    ]
