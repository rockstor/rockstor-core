# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storageadmin', '0012_auto_20200429_1428'),
    ]

    operations = [
        migrations.CreateModel(
            name='BridgeConnection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('docker_name', models.CharField(max_length=64, null=True)),
                ('usercon', models.BooleanField(default=False)),
                ('aux_address', models.CharField(max_length=2048, null=True)),
                ('dgateway', models.CharField(max_length=64, null=True)),
                ('host_binding', models.CharField(max_length=64, null=True)),
                ('icc', models.BooleanField(default=False)),
                ('internal', models.BooleanField(default=False)),
                ('ip_masquerade', models.BooleanField(default=False)),
                ('ip_range', models.CharField(max_length=64, null=True)),
                ('subnet', models.CharField(max_length=64, null=True)),
                ('connection', models.ForeignKey(to='storageadmin.NetworkConnection', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='DContainerNetwork',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('connection', models.ForeignKey(to='storageadmin.BridgeConnection')),
                ('container', models.ForeignKey(to='storageadmin.DContainer')),
            ],
        ),
        migrations.AddField(
            model_name='dport',
            name='publish',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterUniqueTogether(
            name='dcontainerlink',
            unique_together=set([('source', 'destination', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='dcontainernetwork',
            unique_together=set([('container', 'connection')]),
        ),
    ]
