# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storageadmin', '0009_auto_20200210_1948'),
    ]

    operations = [
        migrations.AddField(
            model_name='sambashare',
            name='time_machine',
            field=models.BooleanField(default=False),
        ),
    ]
