# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-02-04 21:50
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sigma_core', '0017_user_photo'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupPost',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='sigma_core.Group')),
            ],
        ),
        migrations.CreateModel(
            name='Publication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('title', models.CharField(max_length=255)),
                ('body', models.TextField()),
                ('poster_group', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_publications', to='sigma_core.Group')),
                ('poster_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_publications', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='grouppost',
            name='publication',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='sigma_publications.Publication'),
        ),
    ]