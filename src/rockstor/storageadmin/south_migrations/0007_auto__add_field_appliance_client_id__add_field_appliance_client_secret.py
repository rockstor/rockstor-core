# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Appliance.client_id'
        db.add_column(u'storageadmin_appliance', 'client_id',
                      self.gf('django.db.models.fields.CharField')(max_length=100, null=True),
                      keep_default=False)

        # Adding field 'Appliance.client_secret'
        db.add_column(u'storageadmin_appliance', 'client_secret',
                      self.gf('django.db.models.fields.CharField')(max_length=255, null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Appliance.client_id'
        db.delete_column(u'storageadmin_appliance', 'client_id')

        # Deleting field 'Appliance.client_secret'
        db.delete_column(u'storageadmin_appliance', 'client_secret')


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
        u'oauth2_provider.application': {
            'Meta': {'object_name': 'Application'},
            'authorization_grant_type': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'client_id': ('django.db.models.fields.CharField', [], {'default': "u'Lhmop5iAurBvi36F=c-L=DP7_OO0RyNd_dl?k40m'", 'unique': 'True', 'max_length': '100'}),
            'client_secret': ('django.db.models.fields.CharField', [], {'default': "u'.De!HqKcBgX8U1?F=Ff7CA4;yuVCvVmo2x6nDG21IBcWTU.8m=L4Ej@1Jv.;Cfvwvp50YFQ!?arppXUbKhcpJiK5c!8z_JvDxl.KDy!hLgcYN2zUMya-QVj!r!C_w?s!'", 'max_length': '255', 'blank': 'True'}),
            'client_type': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'redirect_uris': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        'storageadmin.advancednfsexport': {
            'Meta': {'object_name': 'AdvancedNFSExport'},
            'export_str': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'storageadmin.apikeys': {
            'Meta': {'object_name': 'APIKeys'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'user': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '8'})
        },
        'storageadmin.appliance': {
            'Meta': {'object_name': 'Appliance'},
            'client_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'client_secret': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
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
            'size': ('django.db.models.fields.BigIntegerField', [], {'default': '0'})
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
            'dns_servers': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'gateway': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
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
            'admin_host': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'editable': ('django.db.models.fields.CharField', [], {'default': "'rw'", 'max_length': '2'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'host_str': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mount_security': ('django.db.models.fields.CharField', [], {'default': "'insecure'", 'max_length': '8'}),
            'nohide': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'syncable': ('django.db.models.fields.CharField', [], {'default': "'async'", 'max_length': '5'})
        },
        'storageadmin.oauthapp': {
            'Meta': {'object_name': 'OauthApp'},
            'application': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['oauth2_provider.Application']", 'unique': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.User']"})
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
            'size': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'toc': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'})
        },
        'storageadmin.poolscrub': {
            'Meta': {'object_name': 'PoolScrub'},
            'end_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'errors': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kb_scrubbed': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'pid': ('django.db.models.fields.IntegerField', [], {}),
            'pool': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Pool']"}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'started'", 'max_length': '10'})
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
            'size': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'subvol_name': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'toc': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'})
        },
        'storageadmin.snapshot': {
            'Meta': {'unique_together': "(('share', 'name'),)", 'object_name': 'Snapshot'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'qgroup': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'real_name': ('django.db.models.fields.CharField', [], {'default': "'unknownsnap'", 'max_length': '4096'}),
            'share': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Share']"}),
            'size': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
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