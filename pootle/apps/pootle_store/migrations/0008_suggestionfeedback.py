# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0007_case_sensitive_schema'),
    ]

    operations = [
        migrations.CreateModel(
            name='SuggestionFeedback',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('comment', models.TextField(null=True)),
                ('suggestion', models.ForeignKey(to='pootle_store.Suggestion')),
            ],
        ),
    ]
