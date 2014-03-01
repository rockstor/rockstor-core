# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'BackupPolicy', fields ['dest_share']
        db.delete_unique(u'backup_backuppolicy', ['dest_share'])

        # Removing unique constraint on 'BackupPolicy', fields ['source_path']
        db.delete_unique(u'backup_backuppolicy', ['source_path'])

        # Removing unique constraint on 'BackupPolicy', fields ['source_ip']
        db.delete_unique(u'backup_backuppolicy', ['source_ip'])

        # Adding field 'BackupPolicy.enabled'
        db.add_column(u'backup_backuppolicy', 'enabled',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)

        # Adding unique constraint on 'BackupPolicy', fields ['source_ip', 'source_path']
        db.create_unique(u'backup_backuppolicy', ['source_ip', 'source_path'])


    def backwards(self, orm):
        # Removing unique constraint on 'BackupPolicy', fields ['source_ip', 'source_path']
        db.delete_unique(u'backup_backuppolicy', ['source_ip', 'source_path'])

        # Deleting field 'BackupPolicy.enabled'
        db.delete_column(u'backup_backuppolicy', 'enabled')

        # Adding unique constraint on 'BackupPolicy', fields ['source_ip']
        db.create_unique(u'backup_backuppolicy', ['source_ip'])

        # Adding unique constraint on 'BackupPolicy', fields ['source_path']
        db.create_unique(u'backup_backuppolicy', ['source_path'])

        # Adding unique constraint on 'BackupPolicy', fields ['dest_share']
        db.create_unique(u'backup_backuppolicy', ['dest_share'])


    models = {
        'backup.backuppolicy': {
            'Meta': {'unique_together': "(('source_ip', 'source_path'),)", 'object_name': 'BackupPolicy'},
            'dest_share': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'frequency': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'notify_email': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '4096'}),
            'num_retain': ('django.db.models.fields.IntegerField', [], {}),
            'source_ip': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'source_path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['backup']