# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Pool'
        db.create_table(u'storageadmin_pool', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=4096)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=100, null=True)),
            ('size', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('raid', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('toc', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('storageadmin', ['Pool'])

        # Adding model 'Disk'
        db.create_table(u'storageadmin_disk', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pool', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storageadmin.Pool'], null=True, on_delete=models.SET_NULL)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=10)),
            ('size', self.gf('django.db.models.fields.IntegerField')()),
            ('offline', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('parted', self.gf('django.db.models.fields.BooleanField')()),
        ))
        db.send_create_signal('storageadmin', ['Disk'])

        # Adding model 'Share'
        db.create_table(u'storageadmin_share', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pool', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storageadmin.Pool'])),
            ('qgroup', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=4096)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=100, null=True)),
            ('size', self.gf('django.db.models.fields.IntegerField')()),
            ('owner', self.gf('django.db.models.fields.CharField')(default='root', max_length=4096)),
            ('group', self.gf('django.db.models.fields.CharField')(default='root', max_length=4096)),
            ('perms', self.gf('django.db.models.fields.CharField')(default='755', max_length=9)),
            ('toc', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('subvol_name', self.gf('django.db.models.fields.CharField')(max_length=4096)),
            ('replica', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('storageadmin', ['Share'])

        # Adding model 'Snapshot'
        db.create_table(u'storageadmin_snapshot', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('share', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storageadmin.Share'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=4096)),
            ('real_name', self.gf('django.db.models.fields.CharField')(default='unknownsnap', max_length=4096)),
            ('writable', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('size', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('toc', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('qgroup', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('uvisible', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('snap_type', self.gf('django.db.models.fields.CharField')(default='admin', max_length=64)),
        ))
        db.send_create_signal('storageadmin', ['Snapshot'])

        # Adding unique constraint on 'Snapshot', fields ['share', 'name']
        db.create_unique(u'storageadmin_snapshot', ['share_id', 'name'])

        # Adding model 'PoolStatistic'
        db.create_table(u'storageadmin_poolstatistic', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pool', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storageadmin.Pool'])),
            ('total_capacity', self.gf('django.db.models.fields.IntegerField')()),
            ('used', self.gf('django.db.models.fields.IntegerField')()),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('storageadmin', ['PoolStatistic'])

        # Adding model 'ShareStatistic'
        db.create_table(u'storageadmin_sharestatistic', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('share', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storageadmin.Share'])),
            ('total_capacity', self.gf('django.db.models.fields.IntegerField')()),
            ('used', self.gf('django.db.models.fields.IntegerField')()),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('storageadmin', ['ShareStatistic'])

        # Adding model 'NFSExportGroup'
        db.create_table(u'storageadmin_nfsexportgroup', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('host_str', self.gf('django.db.models.fields.CharField')(max_length=4096)),
            ('editable', self.gf('django.db.models.fields.CharField')(default='ro', max_length=2)),
            ('syncable', self.gf('django.db.models.fields.CharField')(default='async', max_length=5)),
            ('mount_security', self.gf('django.db.models.fields.CharField')(default='insecure', max_length=8)),
            ('nohide', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('storageadmin', ['NFSExportGroup'])

        # Adding model 'NFSExport'
        db.create_table(u'storageadmin_nfsexport', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('export_group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storageadmin.NFSExportGroup'])),
            ('share', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storageadmin.Share'])),
            ('mount', self.gf('django.db.models.fields.CharField')(max_length=4096)),
        ))
        db.send_create_signal('storageadmin', ['NFSExport'])

        # Adding model 'SambaShare'
        db.create_table(u'storageadmin_sambashare', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('share', self.gf('django.db.models.fields.related.OneToOneField')(related_name='sambashare', unique=True, to=orm['storageadmin.Share'])),
            ('path', self.gf('django.db.models.fields.CharField')(unique=True, max_length=4096)),
            ('comment', self.gf('django.db.models.fields.CharField')(default='foo bar', max_length=100)),
            ('browsable', self.gf('django.db.models.fields.CharField')(default='yes', max_length=3)),
            ('read_only', self.gf('django.db.models.fields.CharField')(default='no', max_length=3)),
            ('guest_ok', self.gf('django.db.models.fields.CharField')(default='no', max_length=3)),
            ('create_mask', self.gf('django.db.models.fields.CharField')(default='0755', max_length=4)),
            ('admin_users', self.gf('django.db.models.fields.CharField')(default='Administrator', max_length=128)),
        ))
        db.send_create_signal('storageadmin', ['SambaShare'])

        # Adding model 'IscsiTarget'
        db.create_table(u'storageadmin_iscsitarget', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('share', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storageadmin.Share'])),
            ('tid', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('tname', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('dev_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('dev_size', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('storageadmin', ['IscsiTarget'])

        # Adding model 'PosixACLs'
        db.create_table(u'storageadmin_posixacls', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('smb_share', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storageadmin.SambaShare'])),
            ('owner', self.gf('django.db.models.fields.CharField')(max_length=5)),
            ('perms', self.gf('django.db.models.fields.CharField')(max_length=3)),
        ))
        db.send_create_signal('storageadmin', ['PosixACLs'])

        # Adding model 'APIKeys'
        db.create_table(u'storageadmin_apikeys', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.CharField')(unique=True, max_length=8)),
            ('key', self.gf('django.db.models.fields.CharField')(unique=True, max_length=10)),
        ))
        db.send_create_signal('storageadmin', ['APIKeys'])

        # Adding model 'Appliance'
        db.create_table(u'storageadmin_appliance', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
            ('ip', self.gf('django.db.models.fields.CharField')(unique=True, max_length=4096)),
            ('current_appliance', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('hostname', self.gf('django.db.models.fields.CharField')(default='Rockstor', max_length=128)),
            ('mgmt_port', self.gf('django.db.models.fields.IntegerField')(default=443)),
        ))
        db.send_create_signal('storageadmin', ['Appliance'])

        # Adding model 'SupportCase'
        db.create_table(u'storageadmin_supportcase', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('notes', self.gf('django.db.models.fields.TextField')()),
            ('zipped_log', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=9)),
            ('case_type', self.gf('django.db.models.fields.CharField')(max_length=6)),
        ))
        db.send_create_signal('storageadmin', ['SupportCase'])

        # Adding model 'DashboardConfig'
        db.create_table(u'storageadmin_dashboardconfig', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
            ('widgets', self.gf('django.db.models.fields.CharField')(max_length=4096)),
        ))
        db.send_create_signal('storageadmin', ['DashboardConfig'])

        # Adding model 'NetworkInterface'
        db.create_table(u'storageadmin_networkinterface', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('alias', self.gf('django.db.models.fields.CharField')(max_length=100, null=True)),
            ('mac', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('boot_proto', self.gf('django.db.models.fields.CharField')(max_length=100, null=True)),
            ('onboot', self.gf('django.db.models.fields.CharField')(max_length=100, null=True)),
            ('network', self.gf('django.db.models.fields.CharField')(max_length=100, null=True)),
            ('netmask', self.gf('django.db.models.fields.CharField')(max_length=100, null=True)),
            ('ipaddr', self.gf('django.db.models.fields.CharField')(max_length=100, null=True)),
            ('itype', self.gf('django.db.models.fields.CharField')(default='io', max_length=100)),
        ))
        db.send_create_signal('storageadmin', ['NetworkInterface'])

        # Adding model 'User'
        db.create_table(u'storageadmin_user', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(related_name='suser', unique=True, null=True, to=orm['auth.User'])),
            ('username', self.gf('django.db.models.fields.CharField')(default='', unique=True, max_length=4096)),
            ('uid', self.gf('django.db.models.fields.IntegerField')(default=5000)),
            ('gid', self.gf('django.db.models.fields.IntegerField')(default=5000)),
        ))
        db.send_create_signal('storageadmin', ['User'])

        # Adding model 'PoolScrub'
        db.create_table(u'storageadmin_poolscrub', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pool', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storageadmin.Pool'])),
            ('status', self.gf('django.db.models.fields.CharField')(default='started', max_length=10)),
            ('pid', self.gf('django.db.models.fields.IntegerField')()),
            ('start_time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('end_time', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('kb_scrubbed', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('errors', self.gf('django.db.models.fields.IntegerField')(null=True)),
        ))
        db.send_create_signal('storageadmin', ['PoolScrub'])

        # Adding model 'Setup'
        db.create_table(u'storageadmin_setup', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('setup_user', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('setup_system', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('setup_disks', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('setup_network', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('storageadmin', ['Setup'])

        # Adding model 'SFTP'
        db.create_table(u'storageadmin_sftp', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('share', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['storageadmin.Share'], unique=True)),
            ('editable', self.gf('django.db.models.fields.CharField')(default='ro', max_length=2)),
        ))
        db.send_create_signal('storageadmin', ['SFTP'])

        # Adding model 'Plugin'
        db.create_table(u'storageadmin_plugin', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=4096)),
            ('display_name', self.gf('django.db.models.fields.CharField')(default='', unique=True, max_length=4096)),
            ('description', self.gf('django.db.models.fields.CharField')(default='', max_length=4096)),
            ('css_file_name', self.gf('django.db.models.fields.CharField')(max_length=4096)),
            ('js_file_name', self.gf('django.db.models.fields.CharField')(max_length=4096)),
            ('key', self.gf('django.db.models.fields.CharField')(unique=True, max_length=4096)),
        ))
        db.send_create_signal('storageadmin', ['Plugin'])

        # Adding model 'InstalledPlugin'
        db.create_table(u'storageadmin_installedplugin', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('plugin_meta', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storageadmin.Plugin'])),
            ('install_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('storageadmin', ['InstalledPlugin'])


    def backwards(self, orm):
        # Removing unique constraint on 'Snapshot', fields ['share', 'name']
        db.delete_unique(u'storageadmin_snapshot', ['share_id', 'name'])

        # Deleting model 'Pool'
        db.delete_table(u'storageadmin_pool')

        # Deleting model 'Disk'
        db.delete_table(u'storageadmin_disk')

        # Deleting model 'Share'
        db.delete_table(u'storageadmin_share')

        # Deleting model 'Snapshot'
        db.delete_table(u'storageadmin_snapshot')

        # Deleting model 'PoolStatistic'
        db.delete_table(u'storageadmin_poolstatistic')

        # Deleting model 'ShareStatistic'
        db.delete_table(u'storageadmin_sharestatistic')

        # Deleting model 'NFSExportGroup'
        db.delete_table(u'storageadmin_nfsexportgroup')

        # Deleting model 'NFSExport'
        db.delete_table(u'storageadmin_nfsexport')

        # Deleting model 'SambaShare'
        db.delete_table(u'storageadmin_sambashare')

        # Deleting model 'IscsiTarget'
        db.delete_table(u'storageadmin_iscsitarget')

        # Deleting model 'PosixACLs'
        db.delete_table(u'storageadmin_posixacls')

        # Deleting model 'APIKeys'
        db.delete_table(u'storageadmin_apikeys')

        # Deleting model 'Appliance'
        db.delete_table(u'storageadmin_appliance')

        # Deleting model 'SupportCase'
        db.delete_table(u'storageadmin_supportcase')

        # Deleting model 'DashboardConfig'
        db.delete_table(u'storageadmin_dashboardconfig')

        # Deleting model 'NetworkInterface'
        db.delete_table(u'storageadmin_networkinterface')

        # Deleting model 'User'
        db.delete_table(u'storageadmin_user')

        # Deleting model 'PoolScrub'
        db.delete_table(u'storageadmin_poolscrub')

        # Deleting model 'Setup'
        db.delete_table(u'storageadmin_setup')

        # Deleting model 'SFTP'
        db.delete_table(u'storageadmin_sftp')

        # Deleting model 'Plugin'
        db.delete_table(u'storageadmin_plugin')

        # Deleting model 'InstalledPlugin'
        db.delete_table(u'storageadmin_installedplugin')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'storageadmin.apikeys': {
            'Meta': {'object_name': 'APIKeys'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'user': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '8'})
        },
        'storageadmin.appliance': {
            'Meta': {'object_name': 'Appliance'},
            'current_appliance': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hostname': ('django.db.models.fields.CharField', [], {'default': "'Rockstor'", 'max_length': '128'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '4096'}),
            'mgmt_port': ('django.db.models.fields.IntegerField', [], {'default': '443'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'})
        },
        'storageadmin.dashboardconfig': {
            'Meta': {'object_name': 'DashboardConfig'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'unique': 'True'}),
            'widgets': ('django.db.models.fields.CharField', [], {'max_length': '4096'})
        },
        'storageadmin.disk': {
            'Meta': {'object_name': 'Disk'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'offline': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'parted': ('django.db.models.fields.BooleanField', [], {}),
            'pool': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Pool']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'size': ('django.db.models.fields.IntegerField', [], {})
        },
        'storageadmin.installedplugin': {
            'Meta': {'object_name': 'InstalledPlugin'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'install_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'plugin_meta': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Plugin']"})
        },
        'storageadmin.iscsitarget': {
            'Meta': {'object_name': 'IscsiTarget'},
            'dev_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'dev_size': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'share': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Share']"}),
            'tid': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'tname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'})
        },
        'storageadmin.networkinterface': {
            'Meta': {'object_name': 'NetworkInterface'},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'boot_proto': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ipaddr': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'itype': ('django.db.models.fields.CharField', [], {'default': "'io'", 'max_length': '100'}),
            'mac': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'netmask': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'network': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'onboot': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'})
        },
        'storageadmin.nfsexport': {
            'Meta': {'object_name': 'NFSExport'},
            'export_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.NFSExportGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mount': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'share': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Share']"})
        },
        'storageadmin.nfsexportgroup': {
            'Meta': {'object_name': 'NFSExportGroup'},
            'editable': ('django.db.models.fields.CharField', [], {'default': "'ro'", 'max_length': '2'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'host_str': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mount_security': ('django.db.models.fields.CharField', [], {'default': "'insecure'", 'max_length': '8'}),
            'nohide': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'syncable': ('django.db.models.fields.CharField', [], {'default': "'async'", 'max_length': '5'})
        },
        'storageadmin.plugin': {
            'Meta': {'object_name': 'Plugin'},
            'css_file_name': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '4096'}),
            'display_name': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '4096'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'js_file_name': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '4096'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '4096'})
        },
        'storageadmin.pool': {
            'Meta': {'object_name': 'Pool'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '4096'}),
            'raid': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'size': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'toc': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'})
        },
        'storageadmin.poolscrub': {
            'Meta': {'object_name': 'PoolScrub'},
            'end_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'errors': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kb_scrubbed': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'pid': ('django.db.models.fields.IntegerField', [], {}),
            'pool': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Pool']"}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'started'", 'max_length': '10'})
        },
        'storageadmin.poolstatistic': {
            'Meta': {'object_name': 'PoolStatistic'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pool': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Pool']"}),
            'total_capacity': ('django.db.models.fields.IntegerField', [], {}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'used': ('django.db.models.fields.IntegerField', [], {})
        },
        'storageadmin.posixacls': {
            'Meta': {'object_name': 'PosixACLs'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'perms': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'smb_share': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.SambaShare']"})
        },
        'storageadmin.sambashare': {
            'Meta': {'object_name': 'SambaShare'},
            'admin_users': ('django.db.models.fields.CharField', [], {'default': "'Administrator'", 'max_length': '128'}),
            'browsable': ('django.db.models.fields.CharField', [], {'default': "'yes'", 'max_length': '3'}),
            'comment': ('django.db.models.fields.CharField', [], {'default': "'foo bar'", 'max_length': '100'}),
            'create_mask': ('django.db.models.fields.CharField', [], {'default': "'0755'", 'max_length': '4'}),
            'guest_ok': ('django.db.models.fields.CharField', [], {'default': "'no'", 'max_length': '3'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '4096'}),
            'read_only': ('django.db.models.fields.CharField', [], {'default': "'no'", 'max_length': '3'}),
            'share': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'sambashare'", 'unique': 'True', 'to': "orm['storageadmin.Share']"})
        },
        'storageadmin.setup': {
            'Meta': {'object_name': 'Setup'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'setup_disks': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'setup_network': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'setup_system': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'setup_user': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'storageadmin.sftp': {
            'Meta': {'object_name': 'SFTP'},
            'editable': ('django.db.models.fields.CharField', [], {'default': "'ro'", 'max_length': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'share': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['storageadmin.Share']", 'unique': 'True'})
        },
        'storageadmin.share': {
            'Meta': {'object_name': 'Share'},
            'group': ('django.db.models.fields.CharField', [], {'default': "'root'", 'max_length': '4096'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '4096'}),
            'owner': ('django.db.models.fields.CharField', [], {'default': "'root'", 'max_length': '4096'}),
            'perms': ('django.db.models.fields.CharField', [], {'default': "'755'", 'max_length': '9'}),
            'pool': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Pool']"}),
            'qgroup': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'replica': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'size': ('django.db.models.fields.IntegerField', [], {}),
            'subvol_name': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'toc': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'})
        },
        'storageadmin.sharestatistic': {
            'Meta': {'object_name': 'ShareStatistic'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'share': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Share']"}),
            'total_capacity': ('django.db.models.fields.IntegerField', [], {}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'used': ('django.db.models.fields.IntegerField', [], {})
        },
        'storageadmin.snapshot': {
            'Meta': {'unique_together': "(('share', 'name'),)", 'object_name': 'Snapshot'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'qgroup': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'real_name': ('django.db.models.fields.CharField', [], {'default': "'unknownsnap'", 'max_length': '4096'}),
            'share': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Share']"}),
            'size': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'snap_type': ('django.db.models.fields.CharField', [], {'default': "'admin'", 'max_length': '64'}),
            'toc': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'uvisible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'writable': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'storageadmin.supportcase': {
            'Meta': {'object_name': 'SupportCase'},
            'case_type': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '9'}),
            'zipped_log': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'storageadmin.user': {
            'Meta': {'object_name': 'User'},
            'gid': ('django.db.models.fields.IntegerField', [], {'default': '5000'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'uid': ('django.db.models.fields.IntegerField', [], {'default': '5000'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'suser'", 'unique': 'True', 'null': 'True', 'to': u"orm['auth.User']"}),
            'username': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '4096'})
        }
    }

    complete_apps = ['storageadmin']