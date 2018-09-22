# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storageadmin', '0004_auto_20170523_1140'),
    ]

    operations = [
        migrations.CreateModel(
            name='DContainerDevice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dev', models.CharField(max_length=1024, null=True)),
                ('val', models.CharField(max_length=1024, null=True)),
                ('description', models.CharField(max_length=2048, null=True)),
                ('label', models.CharField(max_length=64, null=True)),
                ('container', models.ForeignKey(to='storageadmin.DContainer')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='dcontainerenv',
            unique_together=set([]),
        ),
        migrations.AlterUniqueTogether(
            name='dcontainerdevice',
            unique_together=set([('container', 'dev')]),
        ),
    ]
