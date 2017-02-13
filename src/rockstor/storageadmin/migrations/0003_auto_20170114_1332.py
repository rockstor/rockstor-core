# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storageadmin', '0002_auto_20161125_0051'),
    ]

    operations = [
        migrations.AddField(
            model_name='share',
            name='pqgroup_eusage',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='share',
            name='pqgroup_rusage',
            field=models.BigIntegerField(default=0),
        ),
    ]
