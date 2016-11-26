# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('storageadmin', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dashboardconfig',
            name='user',
            field=models.OneToOneField(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='user',
            name='smb_shares',
            field=models.ManyToManyField(related_name='admin_users', to='storageadmin.SambaShare'),
        ),
    ]
