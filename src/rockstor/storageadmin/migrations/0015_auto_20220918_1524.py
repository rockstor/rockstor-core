# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storageadmin', '0014_rockon_taskid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='poolscrub',
            name='csum_discards',
            field=models.BigIntegerField(default=0),
        ),
    ]