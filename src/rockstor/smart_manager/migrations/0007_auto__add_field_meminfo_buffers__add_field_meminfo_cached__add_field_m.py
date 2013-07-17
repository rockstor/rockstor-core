# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'MemInfo.buffers'
        db.add_column('smart_manager_meminfo', 'buffers',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)

        # Adding field 'MemInfo.cached'
        db.add_column('smart_manager_meminfo', 'cached',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)

        # Adding field 'MemInfo.swap_total'
        db.add_column('smart_manager_meminfo', 'swap_total',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)

        # Adding field 'MemInfo.swap_free'
        db.add_column('smart_manager_meminfo', 'swap_free',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)

        # Adding field 'MemInfo.active'
        db.add_column('smart_manager_meminfo', 'active',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)

        # Adding field 'MemInfo.inactive'
        db.add_column('smart_manager_meminfo', 'inactive',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)

        # Adding field 'MemInfo.dirty'
        db.add_column('smart_manager_meminfo', 'dirty',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'MemInfo.buffers'
        db.delete_column('smart_manager_meminfo', 'buffers')

        # Deleting field 'MemInfo.cached'
        db.delete_column('smart_manager_meminfo', 'cached')

        # Deleting field 'MemInfo.swap_total'
        db.delete_column('smart_manager_meminfo', 'swap_total')

        # Deleting field 'MemInfo.swap_free'
        db.delete_column('smart_manager_meminfo', 'swap_free')

        # Deleting field 'MemInfo.active'
        db.delete_column('smart_manager_meminfo', 'active')

        # Deleting field 'MemInfo.inactive'
        db.delete_column('smart_manager_meminfo', 'inactive')

        # Deleting field 'MemInfo.dirty'
        db.delete_column('smart_manager_meminfo', 'dirty')


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
        'smart_manager.poolusage': {
            'Meta': {'object_name': 'PoolUsage'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pool': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'usage': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'smart_manager.service': {
            'Meta': {'object_name': 'Service'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '24'}),
            'registered': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'smart_manager.servicestatus': {
            'Meta': {'object_name': 'ServiceStatus'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smart_manager.Service']"}),
            'status': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'smart_manager.sprobe': {
            'Meta': {'object_name': 'SProbe'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'smart': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '7'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'smart_manager.vmstat': {
            'Meta': {'object_name': 'VmStat'},
            'free_pages': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['smart_manager']