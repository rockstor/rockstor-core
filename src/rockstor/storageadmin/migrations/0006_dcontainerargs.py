# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storageadmin', '0005_auto_20180913_0923'),
    ]

    operations = [
        migrations.CreateModel(
            name='DContainerArgs',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=1024)),
                ('val', models.CharField(max_length=1024, blank=True)),
                ('container', models.ForeignKey(to='storageadmin.DContainer')),
            ],
        ),
    ]
