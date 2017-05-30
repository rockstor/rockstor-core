# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storageadmin', '0003_auto_20170114_1332'),
    ]

    operations = [
        migrations.AlterField(
            model_name='disk',
            name='role',
            field=models.CharField(max_length=1024, null=True),
        ),
    ]
