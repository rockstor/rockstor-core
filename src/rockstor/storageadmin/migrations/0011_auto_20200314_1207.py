# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storageadmin', '0010_sambashare_time_machine'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='netatalkshare',
            name='share',
        ),
        migrations.DeleteModel(
            name='NetatalkShare',
        ),
    ]
