# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-19 12:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_translationproject', '0006_relink_or_drop_orphan_translationprojects'),
    ]

    operations = [
        migrations.AddField(
            model_name='translationproject',
            name='awaiting_deletion',
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]