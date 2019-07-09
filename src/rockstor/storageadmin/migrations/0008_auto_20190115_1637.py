# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storageadmin', '0007_auto_20181210_0740'),
    ]

    operations = [
        migrations.AddField(
            model_name='disk',
            name='allocated',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='disk',
            name='devid',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='poolbalance',
            name='internal',
            field=models.BooleanField(default=False),
        ),
    ]
