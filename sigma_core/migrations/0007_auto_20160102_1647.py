# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-01-02 15:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sigma_core', '0006_user_phone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='membership_policy',
            field=models.CharField(choices=[('anyone', 'Anyone can join the group'), ('request', 'Anyone can request to join the group'), ('upon_invitation', 'Can join the group only upon invitation')], default='upon_invitation', max_length=64),
        ),
        migrations.AlterField(
            model_name='group',
            name='type',
            field=models.CharField(choices=[('basic', 'Simple group'), ('cursus', 'Cursus or department'), ('association', 'Association'), ('school_promotion', 'School promotion'), ('school', 'School')], default='basic', max_length=64),
        ),
        migrations.AlterField(
            model_name='group',
            name='validation_policy',
            field=models.CharField(choices=[('admins', 'Only admins can accept join requests or invite members'), ('members', 'Every member can accept join requests or invite members')], default='admins', max_length=64),
        ),
        migrations.AlterField(
            model_name='group',
            name='visibility',
            field=models.CharField(choices=[('public', 'Anyone can see the group'), ('private', 'Group is not visible')], default='private', max_length=64),
        ),
    ]
