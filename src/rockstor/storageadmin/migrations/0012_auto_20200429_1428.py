# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storageadmin', '0011_auto_20200314_1207'),
    ]

    operations = [
        migrations.AddField(
            model_name='poolscrub',
            name='eta',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='poolscrub',
            name='rate',
            field=models.CharField(default=b'', max_length=15),
        ),
        migrations.AddField(
            model_name='poolscrub',
            name='time_left',
            field=models.BigIntegerField(default=0),
        ),
    ]
