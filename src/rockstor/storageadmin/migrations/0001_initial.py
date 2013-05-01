# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Pool'
        db.create_table('storageadmin_pool', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=4096)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=100, null=True)),
            ('size', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('raid', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal('storageadmin', ['Pool'])

        # Adding model 'Disk'
        db.create_table('storageadmin_disk', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pool', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storageadmin.Pool'], null=True, on_delete=models.SET_NULL)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=10)),
            ('size', self.gf('django.db.models.fields.IntegerField')()),
            ('free', self.gf('django.db.models.fields.IntegerField')()),
            ('parted', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('storageadmin', ['Disk'])

        # Adding model 'Qgroup'
        db.create_table('storageadmin_qgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(unique=True, max_length=4096)),
        ))
        db.send_create_signal('storageadmin', ['Qgroup'])

        # Adding model 'Share'
        db.create_table('storageadmin_share', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pool', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storageadmin.Pool'])),
            ('qgroup', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storageadmin.Qgroup'])),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=4096)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=100, null=True)),
            ('size', self.gf('django.db.models.fields.IntegerField')()),
            ('free', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('storageadmin', ['Share'])

        # Adding model 'Snapshot'
        db.create_table('storageadmin_snapshot', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('share', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storageadmin.Share'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=4096)),
            ('writable', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('size', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('storageadmin', ['Snapshot'])

        # Adding unique constraint on 'Snapshot', fields ['share', 'name']
        db.create_unique('storageadmin_snapshot', ['share_id', 'name'])

        # Adding model 'PoolStatistic'
        db.create_table('storageadmin_poolstatistic', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pool', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storageadmin.Pool'])),
            ('total_capacity', self.gf('django.db.models.fields.IntegerField')()),
            ('used', self.gf('django.db.models.fields.IntegerField')()),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('storageadmin', ['PoolStatistic'])

        # Adding model 'ShareStatistic'
        db.create_table('storageadmin_sharestatistic', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('share', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storageadmin.Share'])),
            ('total_capacity', self.gf('django.db.models.fields.IntegerField')()),
            ('used', self.gf('django.db.models.fields.IntegerField')()),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('storageadmin', ['ShareStatistic'])

        # Adding model 'NFSExport'
        db.create_table('storageadmin_nfsexport', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('share', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storageadmin.Share'])),
            ('mount', self.gf('django.db.models.fields.CharField')(max_length=4096)),
            ('host_str', self.gf('django.db.models.fields.CharField')(max_length=4096)),
            ('editable', self.gf('django.db.models.fields.CharField')(default='ro', max_length=2)),
            ('syncable', self.gf('django.db.models.fields.CharField')(default='async', max_length=5)),
            ('mount_security', self.gf('django.db.models.fields.CharField')(default='insecure', max_length=8)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('storageadmin', ['NFSExport'])

        # Adding model 'SambaShare'
        db.create_table('storageadmin_sambashare', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('share', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storageadmin.Share'])),
            ('path', self.gf('django.db.models.fields.CharField')(unique=True, max_length=4096)),
            ('comment', self.gf('django.db.models.fields.CharField')(default='foo bar', max_length=100)),
            ('browsable', self.gf('django.db.models.fields.CharField')(default='yes', max_length=3)),
            ('read_only', self.gf('django.db.models.fields.CharField')(default='no', max_length=3)),
            ('guest_ok', self.gf('django.db.models.fields.CharField')(default='no', max_length=3)),
            ('create_mask', self.gf('django.db.models.fields.CharField')(default='0755', max_length=4)),
        ))
        db.send_create_signal('storageadmin', ['SambaShare'])

        # Adding model 'IscsiTarget'
        db.create_table('storageadmin_iscsitarget', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('share', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storageadmin.Share'])),
            ('tid', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('tname', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('dev_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('dev_size', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('storageadmin', ['IscsiTarget'])

        # Adding model 'PosixACLs'
        db.create_table('storageadmin_posixacls', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('smb_share', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storageadmin.SambaShare'])),
            ('owner', self.gf('django.db.models.fields.CharField')(max_length=5)),
            ('perms', self.gf('django.db.models.fields.CharField')(max_length=3)),
        ))
        db.send_create_signal('storageadmin', ['PosixACLs'])

        # Adding model 'APIKeys'
        db.create_table('storageadmin_apikeys', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.CharField')(unique=True, max_length=8)),
            ('key', self.gf('django.db.models.fields.CharField')(unique=True, max_length=10)),
        ))
        db.send_create_signal('storageadmin', ['APIKeys'])

        # Adding model 'Appliance'
        db.create_table('storageadmin_appliance', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
            ('ip', self.gf('django.db.models.fields.CharField')(unique=True, max_length=4096)),
            ('current_appliance', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('storageadmin', ['Appliance'])

        # Adding model 'SupportCase'
        db.create_table('storageadmin_supportcase', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('notes', self.gf('django.db.models.fields.TextField')()),
            ('zipped_log', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=9)),
            ('case_type', self.gf('django.db.models.fields.CharField')(max_length=6)),
        ))
        db.send_create_signal('storageadmin', ['SupportCase'])

        # Adding model 'DashboardConfig'
        db.create_table('storageadmin_dashboardconfig', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
            ('widgets', self.gf('django.db.models.fields.CharField')(max_length=4096)),
        ))
        db.send_create_signal('storageadmin', ['DashboardConfig'])


    def backwards(self, orm):
        # Removing unique constraint on 'Snapshot', fields ['share', 'name']
        db.delete_unique('storageadmin_snapshot', ['share_id', 'name'])

        # Deleting model 'Pool'
        db.delete_table('storageadmin_pool')

        # Deleting model 'Disk'
        db.delete_table('storageadmin_disk')

        # Deleting model 'Qgroup'
        db.delete_table('storageadmin_qgroup')

        # Deleting model 'Share'
        db.delete_table('storageadmin_share')

        # Deleting model 'Snapshot'
        db.delete_table('storageadmin_snapshot')

        # Deleting model 'PoolStatistic'
        db.delete_table('storageadmin_poolstatistic')

        # Deleting model 'ShareStatistic'
        db.delete_table('storageadmin_sharestatistic')

        # Deleting model 'NFSExport'
        db.delete_table('storageadmin_nfsexport')

        # Deleting model 'SambaShare'
        db.delete_table('storageadmin_sambashare')

        # Deleting model 'IscsiTarget'
        db.delete_table('storageadmin_iscsitarget')

        # Deleting model 'PosixACLs'
        db.delete_table('storageadmin_posixacls')

        # Deleting model 'APIKeys'
        db.delete_table('storageadmin_apikeys')

        # Deleting model 'Appliance'
        db.delete_table('storageadmin_appliance')

        # Deleting model 'SupportCase'
        db.delete_table('storageadmin_supportcase')

        # Deleting model 'DashboardConfig'
        db.delete_table('storageadmin_dashboardconfig')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'storageadmin.apikeys': {
            'Meta': {'object_name': 'APIKeys'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'user': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '8'})
        },
        'storageadmin.appliance': {
            'Meta': {'object_name': 'Appliance'},
            'current_appliance': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '4096'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'})
        },
        'storageadmin.dashboardconfig': {
            'Meta': {'object_name': 'DashboardConfig'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'}),
            'widgets': ('django.db.models.fields.CharField', [], {'max_length': '4096'})
        },
        'storageadmin.disk': {
            'Meta': {'object_name': 'Disk'},
            'free': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'parted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'pool': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Pool']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'size': ('django.db.models.fields.IntegerField', [], {})
        },
        'storageadmin.iscsitarget': {
            'Meta': {'object_name': 'IscsiTarget'},
            'dev_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'dev_size': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'share': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Share']"}),
            'tid': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'tname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'})
        },
        'storageadmin.nfsexport': {
            'Meta': {'object_name': 'NFSExport'},
            'editable': ('django.db.models.fields.CharField', [], {'default': "'ro'", 'max_length': '2'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'host_str': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mount': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'mount_security': ('django.db.models.fields.CharField', [], {'default': "'insecure'", 'max_length': '8'}),
            'share': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Share']"}),
            'syncable': ('django.db.models.fields.CharField', [], {'default': "'async'", 'max_length': '5'})
        },
        'storageadmin.pool': {
            'Meta': {'object_name': 'Pool'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '4096'}),
            'raid': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'size': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'})
        },
        'storageadmin.poolstatistic': {
            'Meta': {'object_name': 'PoolStatistic'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pool': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Pool']"}),
            'total_capacity': ('django.db.models.fields.IntegerField', [], {}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'used': ('django.db.models.fields.IntegerField', [], {})
        },
        'storageadmin.posixacls': {
            'Meta': {'object_name': 'PosixACLs'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'perms': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'smb_share': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.SambaShare']"})
        },
        'storageadmin.qgroup': {
            'Meta': {'object_name': 'Qgroup'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '4096'})
        },
        'storageadmin.sambashare': {
            'Meta': {'object_name': 'SambaShare'},
            'browsable': ('django.db.models.fields.CharField', [], {'default': "'yes'", 'max_length': '3'}),
            'comment': ('django.db.models.fields.CharField', [], {'default': "'foo bar'", 'max_length': '100'}),
            'create_mask': ('django.db.models.fields.CharField', [], {'default': "'0755'", 'max_length': '4'}),
            'guest_ok': ('django.db.models.fields.CharField', [], {'default': "'no'", 'max_length': '3'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '4096'}),
            'read_only': ('django.db.models.fields.CharField', [], {'default': "'no'", 'max_length': '3'}),
            'share': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Share']"})
        },
        'storageadmin.share': {
            'Meta': {'object_name': 'Share'},
            'free': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '4096'}),
            'pool': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Pool']"}),
            'qgroup': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Qgroup']"}),
            'size': ('django.db.models.fields.IntegerField', [], {}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'})
        },
        'storageadmin.sharestatistic': {
            'Meta': {'object_name': 'ShareStatistic'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'share': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Share']"}),
            'total_capacity': ('django.db.models.fields.IntegerField', [], {}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'used': ('django.db.models.fields.IntegerField', [], {})
        },
        'storageadmin.snapshot': {
            'Meta': {'unique_together': "(('share', 'name'),)", 'object_name': 'Snapshot'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'share': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Share']"}),
            'size': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'writable': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'storageadmin.supportcase': {
            'Meta': {'object_name': 'SupportCase'},
            'case_type': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '9'}),
            'zipped_log': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        }
    }

    complete_apps = ['storageadmin']