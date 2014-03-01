# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'PolicyTrail'
        db.create_table(u'backup_policytrail', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('policy', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['backup.BackupPolicy'])),
            ('start', self.gf('django.db.models.fields.DateTimeField')(null=True, db_index=True)),
        ))
        db.send_create_signal('backup', ['PolicyTrail'])


    def backwards(self, orm):
        # Deleting model 'PolicyTrail'
        db.delete_table(u'backup_policytrail')


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
        },
        'backup.policytrail': {
            'Meta': {'object_name': 'PolicyTrail'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'policy': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['backup.BackupPolicy']"}),
            'start': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'})
        }
    }

    complete_apps = ['backup']