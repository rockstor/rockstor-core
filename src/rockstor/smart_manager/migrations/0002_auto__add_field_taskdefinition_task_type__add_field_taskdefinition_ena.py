# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'TaskDefinition.task_type'
        db.add_column('smart_manager_taskdefinition', 'task_type',
                      self.gf('django.db.models.fields.CharField')(default='snapshot', max_length=100),
                      keep_default=False)

        # Adding field 'TaskDefinition.enabled'
        db.add_column('smart_manager_taskdefinition', 'enabled',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)

        # Adding unique constraint on 'TaskDefinition', fields ['name']
        db.create_unique('smart_manager_taskdefinition', ['name'])

        # Deleting field 'Task.name'
        db.delete_column('smart_manager_task', 'name')

        # Deleting field 'Task.json_meta'
        db.delete_column('smart_manager_task', 'json_meta')

        # Adding field 'Task.task_def'
        db.add_column('smart_manager_task', 'task_def',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['smart_manager.TaskDefinition']),
                      keep_default=False)


    def backwards(self, orm):
        # Removing unique constraint on 'TaskDefinition', fields ['name']
        db.delete_unique('smart_manager_taskdefinition', ['name'])

        # Deleting field 'TaskDefinition.task_type'
        db.delete_column('smart_manager_taskdefinition', 'task_type')

        # Deleting field 'TaskDefinition.enabled'
        db.delete_column('smart_manager_taskdefinition', 'enabled')

        # Adding field 'Task.name'
        db.add_column('smart_manager_task', 'name',
                      self.gf('django.db.models.fields.CharField')(default='mysnap123', max_length=255),
                      keep_default=False)

        # Adding field 'Task.json_meta'
        db.add_column('smart_manager_task', 'json_meta',
                      self.gf('django.db.models.fields.CharField')(default={}, max_length=8192),
                      keep_default=False)

        # Deleting field 'Task.task_def'
        db.delete_column('smart_manager_task', 'task_def_id')


    models = {
        'smart_manager.cpumetric': {
            'Meta': {'object_name': 'CPUMetric'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'idle': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'smode': ('django.db.models.fields.IntegerField', [], {}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
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
            'ts': ('django.db.models.fields.DateTimeField', [], {}),
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
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
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
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
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
            'ts': ('django.db.models.fields.DateTimeField', [], {})
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
            'ts': ('django.db.models.fields.DateTimeField', [], {})
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
            'ts': ('django.db.models.fields.DateTimeField', [], {})
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
            'ts': ('django.db.models.fields.DateTimeField', [], {})
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
            'ts': ('django.db.models.fields.DateTimeField', [], {}),
            'uid': ('django.db.models.fields.IntegerField', [], {})
        },
        'smart_manager.poolusage': {
            'Meta': {'object_name': 'PoolUsage'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pool': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
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
            'end_ts': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
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
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'smart_manager.shareusage': {
            'Meta': {'object_name': 'ShareUsage'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'usage': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'smart_manager.sprobe': {
            'Meta': {'object_name': 'SProbe'},
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'smart': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '7'})
        },
        'smart_manager.task': {
            'Meta': {'object_name': 'Task'},
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '7'}),
            'task_def': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smart_manager.TaskDefinition']"})
        },
        'smart_manager.taskdefinition': {
            'Meta': {'object_name': 'TaskDefinition'},
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'frequency': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'json_meta': ('django.db.models.fields.CharField', [], {'max_length': '8192'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'task_type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {})
        },
        'smart_manager.vmstat': {
            'Meta': {'object_name': 'VmStat'},
            'free_pages': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['smart_manager']