# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storageadmin', '0006_dcontainerargs'),
    ]

    operations = [
        migrations.CreateModel(
            name='DContainerLabel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=1024, null=True)),
                ('val', models.CharField(max_length=1024, null=True)),
                ('container', models.ForeignKey(to='storageadmin.DContainer')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='dcontainerlabel',
            unique_together=set([('container', 'val')]),
        ),
    ]
