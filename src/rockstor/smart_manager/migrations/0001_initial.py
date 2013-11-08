# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CPUMetric'
        db.create_table('smart_manager_cpumetric', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('umode', self.gf('django.db.models.fields.IntegerField')()),
            ('umode_nice', self.gf('django.db.models.fields.IntegerField')()),
            ('smode', self.gf('django.db.models.fields.IntegerField')()),
            ('idle', self.gf('django.db.models.fields.IntegerField')()),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('smart_manager', ['CPUMetric'])

        # Adding model 'DiskStat'
        db.create_table('smart_manager_diskstat', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('reads_completed', self.gf('django.db.models.fields.FloatField')()),
            ('reads_merged', self.gf('django.db.models.fields.FloatField')()),
            ('sectors_read', self.gf('django.db.models.fields.FloatField')()),
            ('ms_reading', self.gf('django.db.models.fields.FloatField')()),
            ('writes_completed', self.gf('django.db.models.fields.FloatField')()),
            ('writes_merged', self.gf('django.db.models.fields.FloatField')()),
            ('sectors_written', self.gf('django.db.models.fields.FloatField')()),
            ('ms_writing', self.gf('django.db.models.fields.FloatField')()),
            ('ios_progress', self.gf('django.db.models.fields.FloatField')()),
            ('ms_ios', self.gf('django.db.models.fields.FloatField')()),
            ('weighted_ios', self.gf('django.db.models.fields.FloatField')()),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
        ))
        db.send_create_signal('smart_manager', ['DiskStat'])

        # Adding model 'LoadAvg'
        db.create_table('smart_manager_loadavg', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('load_1', self.gf('django.db.models.fields.FloatField')()),
            ('load_5', self.gf('django.db.models.fields.FloatField')()),
            ('load_15', self.gf('django.db.models.fields.FloatField')()),
            ('active_threads', self.gf('django.db.models.fields.IntegerField')()),
            ('total_threads', self.gf('django.db.models.fields.IntegerField')()),
            ('latest_pid', self.gf('django.db.models.fields.IntegerField')()),
            ('idle_seconds', self.gf('django.db.models.fields.IntegerField')()),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('smart_manager', ['LoadAvg'])

        # Adding model 'MemInfo'
        db.create_table('smart_manager_meminfo', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('total', self.gf('django.db.models.fields.IntegerField')()),
            ('free', self.gf('django.db.models.fields.IntegerField')()),
            ('buffers', self.gf('django.db.models.fields.IntegerField')()),
            ('cached', self.gf('django.db.models.fields.IntegerField')()),
            ('swap_total', self.gf('django.db.models.fields.IntegerField')()),
            ('swap_free', self.gf('django.db.models.fields.IntegerField')()),
            ('active', self.gf('django.db.models.fields.IntegerField')()),
            ('inactive', self.gf('django.db.models.fields.IntegerField')()),
            ('dirty', self.gf('django.db.models.fields.IntegerField')()),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('smart_manager', ['MemInfo'])

        # Adding model 'VmStat'
        db.create_table('smart_manager_vmstat', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('free_pages', self.gf('django.db.models.fields.IntegerField')()),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('smart_manager', ['VmStat'])

        # Adding model 'Service'
        db.create_table('smart_manager_service', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=24)),
            ('display_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=24)),
            ('config', self.gf('django.db.models.fields.CharField')(max_length=8192, null=True)),
        ))
        db.send_create_signal('smart_manager', ['Service'])

        # Adding model 'ServiceStatus'
        db.create_table('smart_manager_servicestatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('service', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smart_manager.Service'])),
            ('status', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('smart_manager', ['ServiceStatus'])

        # Adding model 'SProbe'
        db.create_table('smart_manager_sprobe', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('display_name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('smart', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=7)),
            ('start', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
            ('end', self.gf('django.db.models.fields.DateTimeField')(null=True, db_index=True)),
        ))
        db.send_create_signal('smart_manager', ['SProbe'])

        # Adding model 'NFSDCallDistribution'
        db.create_table('smart_manager_nfsdcalldistribution', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('rid', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smart_manager.SProbe'])),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('num_lookup', self.gf('django.db.models.fields.IntegerField')()),
            ('num_read', self.gf('django.db.models.fields.IntegerField')()),
            ('num_write', self.gf('django.db.models.fields.IntegerField')()),
            ('num_create', self.gf('django.db.models.fields.IntegerField')()),
            ('num_commit', self.gf('django.db.models.fields.IntegerField')()),
            ('num_remove', self.gf('django.db.models.fields.IntegerField')()),
            ('sum_read', self.gf('django.db.models.fields.IntegerField')()),
            ('sum_write', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('smart_manager', ['NFSDCallDistribution'])

        # Adding model 'NFSDClientDistribution'
        db.create_table('smart_manager_nfsdclientdistribution', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('rid', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smart_manager.SProbe'])),
            ('ts', self.gf('django.db.models.fields.DateTimeField')()),
            ('ip', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('num_lookup', self.gf('django.db.models.fields.IntegerField')()),
            ('num_read', self.gf('django.db.models.fields.IntegerField')()),
            ('num_write', self.gf('django.db.models.fields.IntegerField')()),
            ('num_create', self.gf('django.db.models.fields.IntegerField')()),
            ('num_commit', self.gf('django.db.models.fields.IntegerField')()),
            ('num_remove', self.gf('django.db.models.fields.IntegerField')()),
            ('sum_read', self.gf('django.db.models.fields.IntegerField')()),
            ('sum_write', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('smart_manager', ['NFSDClientDistribution'])

        # Adding model 'NFSDShareDistribution'
        db.create_table('smart_manager_nfsdsharedistribution', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('rid', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smart_manager.SProbe'])),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('share', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('num_lookup', self.gf('django.db.models.fields.IntegerField')()),
            ('num_read', self.gf('django.db.models.fields.IntegerField')()),
            ('num_write', self.gf('django.db.models.fields.IntegerField')()),
            ('num_create', self.gf('django.db.models.fields.IntegerField')()),
            ('num_commit', self.gf('django.db.models.fields.IntegerField')()),
            ('num_remove', self.gf('django.db.models.fields.IntegerField')()),
            ('sum_read', self.gf('django.db.models.fields.IntegerField')()),
            ('sum_write', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('smart_manager', ['NFSDShareDistribution'])

        # Adding model 'PoolUsage'
        db.create_table('smart_manager_poolusage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pool', self.gf('django.db.models.fields.CharField')(max_length=4096)),
            ('usage', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('smart_manager', ['PoolUsage'])

        # Adding model 'NetStat'
        db.create_table('smart_manager_netstat', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('device', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('kb_rx', self.gf('django.db.models.fields.FloatField')()),
            ('packets_rx', self.gf('django.db.models.fields.FloatField')()),
            ('errs_rx', self.gf('django.db.models.fields.FloatField')()),
            ('drop_rx', self.gf('django.db.models.fields.IntegerField')()),
            ('fifo_rx', self.gf('django.db.models.fields.IntegerField')()),
            ('frame', self.gf('django.db.models.fields.IntegerField')()),
            ('compressed_rx', self.gf('django.db.models.fields.IntegerField')()),
            ('multicast_rx', self.gf('django.db.models.fields.IntegerField')()),
            ('kb_tx', self.gf('django.db.models.fields.FloatField')()),
            ('packets_tx', self.gf('django.db.models.fields.IntegerField')()),
            ('errs_tx', self.gf('django.db.models.fields.IntegerField')()),
            ('drop_tx', self.gf('django.db.models.fields.IntegerField')()),
            ('fifo_tx', self.gf('django.db.models.fields.IntegerField')()),
            ('colls', self.gf('django.db.models.fields.IntegerField')()),
            ('carrier', self.gf('django.db.models.fields.IntegerField')()),
            ('compressed_tx', self.gf('django.db.models.fields.IntegerField')()),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
        ))
        db.send_create_signal('smart_manager', ['NetStat'])

        # Adding model 'NFSDShareClientDistribution'
        db.create_table('smart_manager_nfsdshareclientdistribution', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('rid', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smart_manager.SProbe'])),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('share', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('client', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('num_lookup', self.gf('django.db.models.fields.IntegerField')()),
            ('num_read', self.gf('django.db.models.fields.IntegerField')()),
            ('num_write', self.gf('django.db.models.fields.IntegerField')()),
            ('num_create', self.gf('django.db.models.fields.IntegerField')()),
            ('num_commit', self.gf('django.db.models.fields.IntegerField')()),
            ('num_remove', self.gf('django.db.models.fields.IntegerField')()),
            ('sum_read', self.gf('django.db.models.fields.IntegerField')()),
            ('sum_write', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('smart_manager', ['NFSDShareClientDistribution'])

        # Adding model 'ShareUsage'
        db.create_table('smart_manager_shareusage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=4096)),
            ('usage', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('smart_manager', ['ShareUsage'])

        # Adding model 'NFSDUidGidDistribution'
        db.create_table('smart_manager_nfsduidgiddistribution', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('rid', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smart_manager.SProbe'])),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('share', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('client', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('uid', self.gf('django.db.models.fields.IntegerField')()),
            ('gid', self.gf('django.db.models.fields.IntegerField')()),
            ('num_lookup', self.gf('django.db.models.fields.IntegerField')()),
            ('num_read', self.gf('django.db.models.fields.IntegerField')()),
            ('num_write', self.gf('django.db.models.fields.IntegerField')()),
            ('num_create', self.gf('django.db.models.fields.IntegerField')()),
            ('num_commit', self.gf('django.db.models.fields.IntegerField')()),
            ('num_remove', self.gf('django.db.models.fields.IntegerField')()),
            ('sum_read', self.gf('django.db.models.fields.IntegerField')()),
            ('sum_write', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('smart_manager', ['NFSDUidGidDistribution'])

        # Adding model 'TaskDefinition'
        db.create_table('smart_manager_taskdefinition', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('frequency', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('json_meta', self.gf('django.db.models.fields.CharField')(max_length=8192)),
        ))
        db.send_create_signal('smart_manager', ['TaskDefinition'])

        # Adding model 'Task'
        db.create_table('smart_manager_task', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('json_meta', self.gf('django.db.models.fields.CharField')(max_length=8192)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=7)),
            ('start', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
            ('end', self.gf('django.db.models.fields.DateTimeField')(null=True, db_index=True)),
        ))
        db.send_create_signal('smart_manager', ['Task'])

        # Adding model 'Replica'
        db.create_table('smart_manager_replica', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('task_name', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('share', self.gf('django.db.models.fields.CharField')(max_length=4096)),
            ('pool', self.gf('django.db.models.fields.CharField')(max_length=4096)),
            ('appliance', self.gf('django.db.models.fields.CharField')(max_length=4096)),
            ('dpool', self.gf('django.db.models.fields.CharField')(max_length=4096)),
            ('dshare', self.gf('django.db.models.fields.CharField')(max_length=4096, null=True)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('frequency', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('smart_manager', ['Replica'])

        # Adding model 'ReplicaTrail'
        db.create_table('smart_manager_replicatrail', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('replica', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smart_manager.Replica'])),
            ('snap_name', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('kb_sent', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('snapshot_created', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('snapshot_failed', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('send_pending', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('send_succeeded', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('send_failed', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('end_ts', self.gf('django.db.models.fields.DateTimeField')(null=True, db_index=True)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('error', self.gf('django.db.models.fields.CharField')(max_length=4096, null=True)),
        ))
        db.send_create_signal('smart_manager', ['ReplicaTrail'])


    def backwards(self, orm):
        # Deleting model 'CPUMetric'
        db.delete_table('smart_manager_cpumetric')

        # Deleting model 'DiskStat'
        db.delete_table('smart_manager_diskstat')

        # Deleting model 'LoadAvg'
        db.delete_table('smart_manager_loadavg')

        # Deleting model 'MemInfo'
        db.delete_table('smart_manager_meminfo')

        # Deleting model 'VmStat'
        db.delete_table('smart_manager_vmstat')

        # Deleting model 'Service'
        db.delete_table('smart_manager_service')

        # Deleting model 'ServiceStatus'
        db.delete_table('smart_manager_servicestatus')

        # Deleting model 'SProbe'
        db.delete_table('smart_manager_sprobe')

        # Deleting model 'NFSDCallDistribution'
        db.delete_table('smart_manager_nfsdcalldistribution')

        # Deleting model 'NFSDClientDistribution'
        db.delete_table('smart_manager_nfsdclientdistribution')

        # Deleting model 'NFSDShareDistribution'
        db.delete_table('smart_manager_nfsdsharedistribution')

        # Deleting model 'PoolUsage'
        db.delete_table('smart_manager_poolusage')

        # Deleting model 'NetStat'
        db.delete_table('smart_manager_netstat')

        # Deleting model 'NFSDShareClientDistribution'
        db.delete_table('smart_manager_nfsdshareclientdistribution')

        # Deleting model 'ShareUsage'
        db.delete_table('smart_manager_shareusage')

        # Deleting model 'NFSDUidGidDistribution'
        db.delete_table('smart_manager_nfsduidgiddistribution')

        # Deleting model 'TaskDefinition'
        db.delete_table('smart_manager_taskdefinition')

        # Deleting model 'Task'
        db.delete_table('smart_manager_task')

        # Deleting model 'Replica'
        db.delete_table('smart_manager_replica')

        # Deleting model 'ReplicaTrail'
        db.delete_table('smart_manager_replicatrail')


    models = {
        'smart_manager.cpumetric': {
            'Meta': {'object_name': 'CPUMetric'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'idle': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'smode': ('django.db.models.fields.IntegerField', [], {}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'umode': ('django.db.models.fields.IntegerField', [], {}),
            'umode_nice': ('django.db.models.fields.IntegerField', [], {})
        },
        'smart_manager.diskstat': {
            'Meta': {'object_name': 'DiskStat'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ios_progress': ('django.db.models.fields.FloatField', [], {}),
            'ms_ios': ('django.db.models.fields.FloatField', [], {}),
            'ms_reading': ('django.db.models.fields.FloatField', [], {}),
            'ms_writing': ('django.db.models.fields.FloatField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'reads_completed': ('django.db.models.fields.FloatField', [], {}),
            'reads_merged': ('django.db.models.fields.FloatField', [], {}),
            'sectors_read': ('django.db.models.fields.FloatField', [], {}),
            'sectors_written': ('django.db.models.fields.FloatField', [], {}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'weighted_ios': ('django.db.models.fields.FloatField', [], {}),
            'writes_completed': ('django.db.models.fields.FloatField', [], {}),
            'writes_merged': ('django.db.models.fields.FloatField', [], {})
        },
        'smart_manager.loadavg': {
            'Meta': {'object_name': 'LoadAvg'},
            'active_threads': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'idle_seconds': ('django.db.models.fields.IntegerField', [], {}),
            'latest_pid': ('django.db.models.fields.IntegerField', [], {}),
            'load_1': ('django.db.models.fields.FloatField', [], {}),
            'load_15': ('django.db.models.fields.FloatField', [], {}),
            'load_5': ('django.db.models.fields.FloatField', [], {}),
            'total_threads': ('django.db.models.fields.IntegerField', [], {}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'})
        },
        'smart_manager.meminfo': {
            'Meta': {'object_name': 'MemInfo'},
            'active': ('django.db.models.fields.IntegerField', [], {}),
            'buffers': ('django.db.models.fields.IntegerField', [], {}),
            'cached': ('django.db.models.fields.IntegerField', [], {}),
            'dirty': ('django.db.models.fields.IntegerField', [], {}),
            'free': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inactive': ('django.db.models.fields.IntegerField', [], {}),
            'swap_free': ('django.db.models.fields.IntegerField', [], {}),
            'swap_total': ('django.db.models.fields.IntegerField', [], {}),
            'total': ('django.db.models.fields.IntegerField', [], {}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'})
        },
        'smart_manager.netstat': {
            'Meta': {'object_name': 'NetStat'},
            'carrier': ('django.db.models.fields.IntegerField', [], {}),
            'colls': ('django.db.models.fields.IntegerField', [], {}),
            'compressed_rx': ('django.db.models.fields.IntegerField', [], {}),
            'compressed_tx': ('django.db.models.fields.IntegerField', [], {}),
            'device': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'drop_rx': ('django.db.models.fields.IntegerField', [], {}),
            'drop_tx': ('django.db.models.fields.IntegerField', [], {}),
            'errs_rx': ('django.db.models.fields.FloatField', [], {}),
            'errs_tx': ('django.db.models.fields.IntegerField', [], {}),
            'fifo_rx': ('django.db.models.fields.IntegerField', [], {}),
            'fifo_tx': ('django.db.models.fields.IntegerField', [], {}),
            'frame': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kb_rx': ('django.db.models.fields.FloatField', [], {}),
            'kb_tx': ('django.db.models.fields.FloatField', [], {}),
            'multicast_rx': ('django.db.models.fields.IntegerField', [], {}),
            'packets_rx': ('django.db.models.fields.FloatField', [], {}),
            'packets_tx': ('django.db.models.fields.IntegerField', [], {}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'})
        },
        'smart_manager.nfsdcalldistribution': {
            'Meta': {'object_name': 'NFSDCallDistribution'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_commit': ('django.db.models.fields.IntegerField', [], {}),
            'num_create': ('django.db.models.fields.IntegerField', [], {}),
            'num_lookup': ('django.db.models.fields.IntegerField', [], {}),
            'num_read': ('django.db.models.fields.IntegerField', [], {}),
            'num_remove': ('django.db.models.fields.IntegerField', [], {}),
            'num_write': ('django.db.models.fields.IntegerField', [], {}),
            'rid': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smart_manager.SProbe']"}),
            'sum_read': ('django.db.models.fields.IntegerField', [], {}),
            'sum_write': ('django.db.models.fields.IntegerField', [], {}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'})
        },
        'smart_manager.nfsdclientdistribution': {
            'Meta': {'object_name': 'NFSDClientDistribution'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'num_commit': ('django.db.models.fields.IntegerField', [], {}),
            'num_create': ('django.db.models.fields.IntegerField', [], {}),
            'num_lookup': ('django.db.models.fields.IntegerField', [], {}),
            'num_read': ('django.db.models.fields.IntegerField', [], {}),
            'num_remove': ('django.db.models.fields.IntegerField', [], {}),
            'num_write': ('django.db.models.fields.IntegerField', [], {}),
            'rid': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smart_manager.SProbe']"}),
            'sum_read': ('django.db.models.fields.IntegerField', [], {}),
            'sum_write': ('django.db.models.fields.IntegerField', [], {}),
            'ts': ('django.db.models.fields.DateTimeField', [], {})
        },
        'smart_manager.nfsdshareclientdistribution': {
            'Meta': {'object_name': 'NFSDShareClientDistribution'},
            'client': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_commit': ('django.db.models.fields.IntegerField', [], {}),
            'num_create': ('django.db.models.fields.IntegerField', [], {}),
            'num_lookup': ('django.db.models.fields.IntegerField', [], {}),
            'num_read': ('django.db.models.fields.IntegerField', [], {}),
            'num_remove': ('django.db.models.fields.IntegerField', [], {}),
            'num_write': ('django.db.models.fields.IntegerField', [], {}),
            'rid': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smart_manager.SProbe']"}),
            'share': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'sum_read': ('django.db.models.fields.IntegerField', [], {}),
            'sum_write': ('django.db.models.fields.IntegerField', [], {}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'})
        },
        'smart_manager.nfsdsharedistribution': {
            'Meta': {'object_name': 'NFSDShareDistribution'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_commit': ('django.db.models.fields.IntegerField', [], {}),
            'num_create': ('django.db.models.fields.IntegerField', [], {}),
            'num_lookup': ('django.db.models.fields.IntegerField', [], {}),
            'num_read': ('django.db.models.fields.IntegerField', [], {}),
            'num_remove': ('django.db.models.fields.IntegerField', [], {}),
            'num_write': ('django.db.models.fields.IntegerField', [], {}),
            'rid': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smart_manager.SProbe']"}),
            'share': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'sum_read': ('django.db.models.fields.IntegerField', [], {}),
            'sum_write': ('django.db.models.fields.IntegerField', [], {}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'})
        },
        'smart_manager.nfsduidgiddistribution': {
            'Meta': {'object_name': 'NFSDUidGidDistribution'},
            'client': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'gid': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_commit': ('django.db.models.fields.IntegerField', [], {}),
            'num_create': ('django.db.models.fields.IntegerField', [], {}),
            'num_lookup': ('django.db.models.fields.IntegerField', [], {}),
            'num_read': ('django.db.models.fields.IntegerField', [], {}),
            'num_remove': ('django.db.models.fields.IntegerField', [], {}),
            'num_write': ('django.db.models.fields.IntegerField', [], {}),
            'rid': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smart_manager.SProbe']"}),
            'share': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'sum_read': ('django.db.models.fields.IntegerField', [], {}),
            'sum_write': ('django.db.models.fields.IntegerField', [], {}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'uid': ('django.db.models.fields.IntegerField', [], {})
        },
        'smart_manager.poolusage': {
            'Meta': {'object_name': 'PoolUsage'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pool': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'usage': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'smart_manager.replica': {
            'Meta': {'object_name': 'Replica'},
            'appliance': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'dpool': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'dshare': ('django.db.models.fields.CharField', [], {'max_length': '4096', 'null': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'frequency': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pool': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'share': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'task_name': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        },
        'smart_manager.replicatrail': {
            'Meta': {'object_name': 'ReplicaTrail'},
            'end_ts': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'error': ('django.db.models.fields.CharField', [], {'max_length': '4096', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kb_sent': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'replica': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smart_manager.Replica']"}),
            'send_failed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'send_pending': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'send_succeeded': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'snap_name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'snapshot_created': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'snapshot_failed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'smart_manager.service': {
            'Meta': {'object_name': 'Service'},
            'config': ('django.db.models.fields.CharField', [], {'max_length': '8192', 'null': 'True'}),
            'display_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '24'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '24'})
        },
        'smart_manager.servicestatus': {
            'Meta': {'object_name': 'ServiceStatus'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smart_manager.Service']"}),
            'status': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'})
        },
        'smart_manager.shareusage': {
            'Meta': {'object_name': 'ShareUsage'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'usage': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'smart_manager.sprobe': {
            'Meta': {'object_name': 'SProbe'},
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'smart': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '7'})
        },
        'smart_manager.task': {
            'Meta': {'object_name': 'Task'},
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'json_meta': ('django.db.models.fields.CharField', [], {'max_length': '8192'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '7'})
        },
        'smart_manager.taskdefinition': {
            'Meta': {'object_name': 'TaskDefinition'},
            'frequency': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'json_meta': ('django.db.models.fields.CharField', [], {'max_length': '8192'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'})
        },
        'smart_manager.vmstat': {
            'Meta': {'object_name': 'VmStat'},
            'free_pages': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['smart_manager']