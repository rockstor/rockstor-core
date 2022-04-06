# Generated by Django 4.0.3 on 2022-04-06 13:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CPUMetric',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=10)),
                ('umode', models.IntegerField()),
                ('umode_nice', models.IntegerField()),
                ('smode', models.IntegerField()),
                ('idle', models.IntegerField()),
                ('ts', models.DateTimeField(auto_now=True, db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='DiskStat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('reads_completed', models.FloatField()),
                ('reads_merged', models.FloatField()),
                ('sectors_read', models.FloatField()),
                ('ms_reading', models.FloatField()),
                ('writes_completed', models.FloatField()),
                ('writes_merged', models.FloatField()),
                ('sectors_written', models.FloatField()),
                ('ms_writing', models.FloatField()),
                ('ios_progress', models.FloatField()),
                ('ms_ios', models.FloatField()),
                ('weighted_ios', models.FloatField()),
                ('ts', models.DateTimeField(db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='LoadAvg',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('load_1', models.FloatField()),
                ('load_5', models.FloatField()),
                ('load_15', models.FloatField()),
                ('active_threads', models.IntegerField()),
                ('total_threads', models.IntegerField()),
                ('latest_pid', models.IntegerField()),
                ('idle_seconds', models.IntegerField()),
                ('ts', models.DateTimeField(auto_now=True, db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='MemInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total', models.BigIntegerField(default=0)),
                ('free', models.BigIntegerField(default=0)),
                ('buffers', models.BigIntegerField(default=0)),
                ('cached', models.BigIntegerField(default=0)),
                ('swap_total', models.BigIntegerField(default=0)),
                ('swap_free', models.BigIntegerField(default=0)),
                ('active', models.BigIntegerField(default=0)),
                ('inactive', models.BigIntegerField(default=0)),
                ('dirty', models.BigIntegerField(default=0)),
                ('ts', models.DateTimeField(auto_now=True, db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='NetStat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('device', models.CharField(max_length=100)),
                ('kb_rx', models.FloatField()),
                ('packets_rx', models.FloatField()),
                ('errs_rx', models.FloatField()),
                ('drop_rx', models.BigIntegerField(default=0)),
                ('fifo_rx', models.BigIntegerField(default=0)),
                ('frame', models.BigIntegerField(default=0)),
                ('compressed_rx', models.BigIntegerField(default=0)),
                ('multicast_rx', models.BigIntegerField(default=0)),
                ('kb_tx', models.FloatField()),
                ('packets_tx', models.BigIntegerField(default=0)),
                ('errs_tx', models.BigIntegerField(default=0)),
                ('drop_tx', models.BigIntegerField(default=0)),
                ('fifo_tx', models.BigIntegerField(default=0)),
                ('colls', models.BigIntegerField(default=0)),
                ('carrier', models.BigIntegerField(default=0)),
                ('compressed_tx', models.BigIntegerField(default=0)),
                ('ts', models.DateTimeField(db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='PoolUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pool', models.CharField(max_length=4096)),
                ('free', models.BigIntegerField(default=0)),
                ('reclaimable', models.BigIntegerField(default=0)),
                ('ts', models.DateTimeField(auto_now=True, db_index=True)),
                ('count', models.BigIntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='Replica',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_name', models.CharField(max_length=1024)),
                ('share', models.CharField(max_length=4096)),
                ('pool', models.CharField(max_length=4096)),
                ('appliance', models.CharField(max_length=4096)),
                ('dpool', models.CharField(max_length=4096)),
                ('dshare', models.CharField(max_length=4096, null=True)),
                ('enabled', models.BooleanField(default=False)),
                ('data_port', models.IntegerField(default=10002)),
                ('meta_port', models.IntegerField(default=10002)),
                ('ts', models.DateTimeField(db_index=True, null=True)),
                ('crontab', models.CharField(max_length=64, null=True)),
                ('replication_ip', models.CharField(max_length=4096, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ReplicaShare',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('share', models.CharField(max_length=4096, unique=True)),
                ('pool', models.CharField(max_length=4096)),
                ('appliance', models.CharField(max_length=4096)),
                ('src_share', models.CharField(max_length=4096, null=True)),
                ('data_port', models.IntegerField(default=10002)),
                ('meta_port', models.IntegerField(default=10002)),
                ('ts', models.DateTimeField(db_index=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=24, unique=True)),
                ('display_name', models.CharField(max_length=24, unique=True)),
                ('config', models.CharField(max_length=8192, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ShareUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=4096)),
                ('r_usage', models.BigIntegerField(default=0)),
                ('e_usage', models.BigIntegerField(default=0)),
                ('ts', models.DateTimeField(auto_now=True, db_index=True)),
                ('count', models.BigIntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='SProbe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('display_name', models.CharField(max_length=255, null=True)),
                ('smart', models.BooleanField(default=False)),
                ('state', models.CharField(choices=[('created', 'created'), ('error', 'error'), ('running', 'running'), ('stopped', 'stopped')], max_length=7)),
                ('start', models.DateTimeField(auto_now=True, db_index=True)),
                ('end', models.DateTimeField(db_index=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TaskDefinition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('task_type', models.CharField(choices=[('scrub', 'scrub'), ('snapshot', 'snapshot'), ('reboot', 'reboot'), ('shutdown', 'shutdown'), ('suspend', 'suspend'), ('custom', 'custom')], max_length=100)),
                ('json_meta', models.CharField(max_length=8192)),
                ('enabled', models.BooleanField(default=True)),
                ('crontab', models.CharField(max_length=64, null=True)),
                ('crontabwindow', models.CharField(max_length=64, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='VmStat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('free_pages', models.BigIntegerField(default=0)),
                ('ts', models.DateTimeField(auto_now=True, db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.CharField(max_length=64)),
                ('start', models.DateTimeField(db_index=True, null=True)),
                ('end', models.DateTimeField(db_index=True, null=True)),
                ('task_def', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='smart_manager.taskdefinition')),
            ],
        ),
        migrations.CreateModel(
            name='ServiceStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.BooleanField(default=False)),
                ('count', models.BigIntegerField(default=1)),
                ('ts', models.DateTimeField(auto_now=True, db_index=True)),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='smart_manager.service')),
            ],
        ),
        migrations.CreateModel(
            name='ReplicaTrail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('snap_name', models.CharField(max_length=1024)),
                ('kb_sent', models.BigIntegerField(default=0)),
                ('snapshot_created', models.DateTimeField(null=True)),
                ('snapshot_failed', models.DateTimeField(null=True)),
                ('send_pending', models.DateTimeField(null=True)),
                ('send_succeeded', models.DateTimeField(null=True)),
                ('send_failed', models.DateTimeField(null=True)),
                ('end_ts', models.DateTimeField(db_index=True, null=True)),
                ('status', models.CharField(max_length=10)),
                ('error', models.CharField(max_length=4096, null=True)),
                ('replica', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='smart_manager.replica')),
            ],
        ),
        migrations.CreateModel(
            name='ReceiveTrail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('snap_name', models.CharField(max_length=1024)),
                ('kb_received', models.BigIntegerField(default=0)),
                ('receive_pending', models.DateTimeField(null=True)),
                ('receive_succeeded', models.DateTimeField(null=True)),
                ('receive_failed', models.DateTimeField(null=True)),
                ('end_ts', models.DateTimeField(db_index=True, null=True)),
                ('status', models.CharField(max_length=10)),
                ('error', models.CharField(max_length=4096, null=True)),
                ('rshare', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='smart_manager.replicashare')),
            ],
        ),
        migrations.CreateModel(
            name='NFSDUidGidDistribution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ts', models.DateTimeField(db_index=True)),
                ('share', models.CharField(max_length=255)),
                ('client', models.CharField(max_length=100)),
                ('uid', models.IntegerField(default=0)),
                ('gid', models.IntegerField(default=0)),
                ('num_lookup', models.BigIntegerField(default=0)),
                ('num_read', models.BigIntegerField(default=0)),
                ('num_write', models.BigIntegerField(default=0)),
                ('num_create', models.BigIntegerField(default=0)),
                ('num_commit', models.BigIntegerField(default=0)),
                ('num_remove', models.BigIntegerField(default=0)),
                ('sum_read', models.BigIntegerField(default=0)),
                ('sum_write', models.BigIntegerField(default=0)),
                ('rid', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='smart_manager.sprobe')),
            ],
        ),
        migrations.CreateModel(
            name='NFSDShareDistribution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ts', models.DateTimeField(db_index=True)),
                ('share', models.CharField(max_length=255)),
                ('num_lookup', models.BigIntegerField(default=0)),
                ('num_read', models.BigIntegerField(default=0)),
                ('num_write', models.BigIntegerField(default=0)),
                ('num_create', models.BigIntegerField(default=0)),
                ('num_commit', models.BigIntegerField(default=0)),
                ('num_remove', models.BigIntegerField(default=0)),
                ('sum_read', models.BigIntegerField(default=0)),
                ('sum_write', models.BigIntegerField(default=0)),
                ('rid', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='smart_manager.sprobe')),
            ],
        ),
        migrations.CreateModel(
            name='NFSDShareClientDistribution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ts', models.DateTimeField(db_index=True)),
                ('share', models.CharField(max_length=255)),
                ('client', models.CharField(max_length=100)),
                ('num_lookup', models.BigIntegerField(default=0)),
                ('num_read', models.BigIntegerField(default=0)),
                ('num_write', models.BigIntegerField(default=0)),
                ('num_create', models.BigIntegerField(default=0)),
                ('num_commit', models.BigIntegerField(default=0)),
                ('num_remove', models.BigIntegerField(default=0)),
                ('sum_read', models.BigIntegerField(default=0)),
                ('sum_write', models.BigIntegerField(default=0)),
                ('rid', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='smart_manager.sprobe')),
            ],
        ),
        migrations.CreateModel(
            name='NFSDClientDistribution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ts', models.DateTimeField()),
                ('ip', models.CharField(max_length=15)),
                ('num_lookup', models.BigIntegerField(default=0)),
                ('num_read', models.BigIntegerField(default=0)),
                ('num_write', models.BigIntegerField(default=0)),
                ('num_create', models.BigIntegerField(default=0)),
                ('num_commit', models.BigIntegerField(default=0)),
                ('num_remove', models.BigIntegerField(default=0)),
                ('sum_read', models.BigIntegerField(default=0)),
                ('sum_write', models.BigIntegerField(default=0)),
                ('rid', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='smart_manager.sprobe')),
            ],
        ),
        migrations.CreateModel(
            name='NFSDCallDistribution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ts', models.DateTimeField(db_index=True)),
                ('num_lookup', models.BigIntegerField(default=0)),
                ('num_read', models.BigIntegerField(default=0)),
                ('num_write', models.BigIntegerField(default=0)),
                ('num_create', models.BigIntegerField(default=0)),
                ('num_commit', models.BigIntegerField(default=0)),
                ('num_remove', models.BigIntegerField(default=0)),
                ('sum_read', models.BigIntegerField(default=0)),
                ('sum_write', models.BigIntegerField(default=0)),
                ('rid', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='smart_manager.sprobe')),
            ],
        ),
    ]
