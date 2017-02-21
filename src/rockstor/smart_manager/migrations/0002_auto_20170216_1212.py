# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smart_manager', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taskdefinition',
            name='task_type',
            field=models.CharField(max_length=100, choices=[(b'scrub', b'scrub'), (b'snapshot', b'snapshot'), (b'reboot', b'reboot'), (b'shutdown', b'shutdown'), (b'suspend', b'suspend'), (b'custom', b'custom')]),
        ),
    ]
