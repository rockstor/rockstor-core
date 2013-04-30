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
            ('ts', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('smart_manager', ['CPUMetric'])

        # Adding model 'DiskStat'
        db.create_table('smart_manager_diskstat', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('reads_completed', self.gf('django.db.models.fields.IntegerField')()),
            ('reads_merged', self.gf('django.db.models.fields.IntegerField')()),
            ('sectors_read', self.gf('django.db.models.fields.IntegerField')()),
            ('ms_reading', self.gf('django.db.models.fields.IntegerField')()),
            ('writes_completed', self.gf('django.db.models.fields.IntegerField')()),
            ('writes_merged', self.gf('django.db.models.fields.IntegerField')()),
            ('sectors_written', self.gf('django.db.models.fields.IntegerField')()),
            ('ms_writing', self.gf('django.db.models.fields.IntegerField')()),
            ('ios_progress', self.gf('django.db.models.fields.IntegerField')()),
            ('ms_ios', self.gf('django.db.models.fields.IntegerField')()),
            ('weighted_ios', self.gf('django.db.models.fields.IntegerField')()),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
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
            ('ts', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('smart_manager', ['LoadAvg'])

        # Adding model 'MemInfo'
        db.create_table('smart_manager_meminfo', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('total', self.gf('django.db.models.fields.IntegerField')()),
            ('free', self.gf('django.db.models.fields.IntegerField')()),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('smart_manager', ['MemInfo'])

        # Adding model 'VmStat'
        db.create_table('smart_manager_vmstat', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('free_pages', self.gf('django.db.models.fields.IntegerField')()),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('smart_manager', ['VmStat'])

        # Adding model 'Service'
        db.create_table('smart_manager_service', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=24)),
            ('registered', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('smart_manager', ['Service'])

        # Adding model 'ServiceStatus'
        db.create_table('smart_manager_servicestatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('service', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smart_manager.Service'])),
            ('status', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('smart_manager', ['ServiceStatus'])

        # Adding model 'STap'
        db.create_table('smart_manager_stap', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('start', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('end', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=32)),
        ))
        db.send_create_signal('smart_manager', ['STap'])

        # Adding model 'HelloTapTS'
        db.create_table('smart_manager_hellotapts', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('message', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('smart_manager', ['HelloTapTS'])

        # Adding model 'IOStatsTap'
        db.create_table('smart_manager_iostatstap', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('proc_name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('num_open', self.gf('django.db.models.fields.IntegerField')()),
            ('num_read', self.gf('django.db.models.fields.IntegerField')()),
            ('sum_read', self.gf('django.db.models.fields.IntegerField')()),
            ('avg_read', self.gf('django.db.models.fields.IntegerField')()),
            ('num_write', self.gf('django.db.models.fields.IntegerField')()),
            ('sum_write', self.gf('django.db.models.fields.IntegerField')()),
            ('avg_write', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('smart_manager', ['IOStatsTap'])


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

        # Deleting model 'STap'
        db.delete_table('smart_manager_stap')

        # Deleting model 'HelloTapTS'
        db.delete_table('smart_manager_hellotapts')

        # Deleting model 'IOStatsTap'
        db.delete_table('smart_manager_iostatstap')


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
        'smart_manager.hellotapts': {
            'Meta': {'object_name': 'HelloTapTS'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'smart_manager.iostatstap': {
            'Meta': {'object_name': 'IOStatsTap'},
            'avg_read': ('django.db.models.fields.IntegerField', [], {}),
            'avg_write': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_open': ('django.db.models.fields.IntegerField', [], {}),
            'num_read': ('django.db.models.fields.IntegerField', [], {}),
            'num_write': ('django.db.models.fields.IntegerField', [], {}),
            'proc_name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'sum_read': ('django.db.models.fields.IntegerField', [], {}),
            'sum_write': ('django.db.models.fields.IntegerField', [], {})
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
        'smart_manager.stap': {
            'Meta': {'object_name': 'STap'},
            'end': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '16'})
        },
        'smart_manager.vmstat': {
            'Meta': {'object_name': 'VmStat'},
            'free_pages': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['smart_manager']