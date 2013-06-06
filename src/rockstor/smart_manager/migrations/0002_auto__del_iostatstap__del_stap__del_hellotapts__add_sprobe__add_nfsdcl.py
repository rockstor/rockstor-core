# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'IOStatsTap'
        db.delete_table('smart_manager_iostatstap')

        # Deleting model 'STap'
        db.delete_table('smart_manager_stap')

        # Deleting model 'HelloTapTS'
        db.delete_table('smart_manager_hellotapts')

        # Adding model 'SProbe'
        db.create_table('smart_manager_sprobe', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('smart', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=7)),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('smart_manager', ['SProbe'])

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

        # Adding model 'NFSDCallDistribution'
        db.create_table('smart_manager_nfsdcalldistribution', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('rid', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smart_manager.SProbe'])),
            ('ts', self.gf('django.db.models.fields.DateTimeField')()),
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


    def backwards(self, orm):
        # Adding model 'IOStatsTap'
        db.create_table('smart_manager_iostatstap', (
            ('num_open', self.gf('django.db.models.fields.IntegerField')()),
            ('sum_read', self.gf('django.db.models.fields.IntegerField')()),
            ('num_write', self.gf('django.db.models.fields.IntegerField')()),
            ('num_read', self.gf('django.db.models.fields.IntegerField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sum_write', self.gf('django.db.models.fields.IntegerField')()),
            ('proc_name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('avg_write', self.gf('django.db.models.fields.IntegerField')()),
            ('avg_read', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('smart_manager', ['IOStatsTap'])

        # Adding model 'STap'
        db.create_table('smart_manager_stap', (
            ('status', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('end', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('start', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('smart_manager', ['STap'])

        # Adding model 'HelloTapTS'
        db.create_table('smart_manager_hellotapts', (
            ('message', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('smart_manager', ['HelloTapTS'])

        # Deleting model 'SProbe'
        db.delete_table('smart_manager_sprobe')

        # Deleting model 'NFSDClientDistribution'
        db.delete_table('smart_manager_nfsdclientdistribution')

        # Deleting model 'NFSDCallDistribution'
        db.delete_table('smart_manager_nfsdcalldistribution')


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
            'ios_progress': ('django.db.models.fields.IntegerField', [], {}),
            'ms_ios': ('django.db.models.fields.IntegerField', [], {}),
            'ms_reading': ('django.db.models.fields.IntegerField', [], {}),
            'ms_writing': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'reads_completed': ('django.db.models.fields.IntegerField', [], {}),
            'reads_merged': ('django.db.models.fields.IntegerField', [], {}),
            'sectors_read': ('django.db.models.fields.IntegerField', [], {}),
            'sectors_written': ('django.db.models.fields.IntegerField', [], {}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'weighted_ios': ('django.db.models.fields.IntegerField', [], {}),
            'writes_completed': ('django.db.models.fields.IntegerField', [], {}),
            'writes_merged': ('django.db.models.fields.IntegerField', [], {})
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
            'free': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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