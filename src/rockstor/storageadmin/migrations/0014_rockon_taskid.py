# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storageadmin', '0013_auto_20200815_2004'),
    ]

    operations = [
        migrations.AddField(
            model_name='rockon',
            name='taskid',
            field=models.CharField(max_length=36, null=True),
        ),
    ]
