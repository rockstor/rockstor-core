# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storageadmin', '0008_auto_20190115_1637'),
    ]

    operations = [
        migrations.AlterField(
            model_name='disk',
            name='name',
            field=models.CharField(unique=True, max_length=192),
        ),
    ]
