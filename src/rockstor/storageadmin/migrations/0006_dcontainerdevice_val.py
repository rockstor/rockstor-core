# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storageadmin', '0005_auto_20180830_1110'),
    ]

    operations = [
        migrations.AddField(
            model_name='dcontainerdevice',
            name='val',
            field=models.CharField(max_length=1024, null=True),
        ),
    ]
