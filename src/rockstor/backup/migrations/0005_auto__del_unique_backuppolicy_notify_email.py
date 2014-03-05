# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'BackupPolicy', fields ['notify_email']
        db.delete_unique(u'backup_backuppolicy', ['notify_email'])


    def backwards(self, orm):
        # Adding unique constraint on 'BackupPolicy', fields ['notify_email']
        db.create_unique(u'backup_backuppolicy', ['notify_email'])


    models = {
        'backup.backuppolicy': {
            'Meta': {'unique_together': "(('source_ip', 'source_path'),)", 'object_name': 'BackupPolicy'},
            'dest_share': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'frequency': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'notify_email': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'num_retain': ('django.db.models.fields.IntegerField', [], {}),
            'source_ip': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'source_path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'})
        },
        'backup.policytrail': {
            'Meta': {'object_name': 'PolicyTrail'},
            'error': ('django.db.models.fields.CharField', [], {'max_length': '2048', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'policy': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['backup.BackupPolicy']"}),
            'snap_created': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'start'", 'max_length': '255'}),
            'status_ts': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'sync_started': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        }
    }

    complete_apps = ['backup']