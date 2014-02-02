# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'BackupPolicy'
        db.create_table('backup_backuppolicy', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('source_ip', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('source_path', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('dest_share', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('notify_email', self.gf('django.db.models.fields.CharField')(unique=True, max_length=4096)),
            ('start', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
            ('frequency', self.gf('django.db.models.fields.IntegerField')()),
            ('num_retain', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('backup', ['BackupPolicy'])


    def backwards(self, orm):
        # Deleting model 'BackupPolicy'
        db.delete_table('backup_backuppolicy')


    models = {
        'backup.backuppolicy': {
            'Meta': {'object_name': 'BackupPolicy'},
            'dest_share': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'frequency': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'notify_email': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '4096'}),
            'num_retain': ('django.db.models.fields.IntegerField', [], {}),
            'source_ip': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'source_path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['backup']