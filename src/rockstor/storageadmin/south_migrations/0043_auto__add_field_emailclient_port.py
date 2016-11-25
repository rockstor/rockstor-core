# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'EmailClient.port'
        db.add_column(u'storageadmin_emailclient', 'port',
                      self.gf('django.db.models.fields.IntegerField')(default=587),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'EmailClient.port'
        db.delete_column(u'storageadmin_emailclient', 'port')


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
            'client_id': ('django.db.models.fields.CharField', [], {'default': "u'2Din3x7H84XawtNaSik1jSdKv2wSMpKP8vmSaSFV'", 'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
            'client_secret': ('django.db.models.fields.CharField', [], {'default': "u'VxffZ3DckHg9OC2QSPFyy6urLxs4pZzyLVNkcOFJVkCHSjVtkib6ljRZLHst77m9ztEmU6VusbuH0GlB3rjgUEBLEG6xpsU1VClYVM3ncryZvAlkh3plwAH8shoyrBd9'", 'max_length': '255', 'db_index': 'True', 'blank': 'True'}),
            'client_type': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'redirect_uris': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'skip_authorization': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'oauth2_provider_application'", 'to': u"orm['auth.User']"})
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
        'storageadmin.configbackup': {
            'Meta': {'object_name': 'ConfigBackup'},
            'config_backup': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'md5sum': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'}),
            'size': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
        },
        'storageadmin.containeroption': {
            'Meta': {'object_name': 'ContainerOption'},
            'container': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.DContainer']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'val': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'})
        },
        'storageadmin.dashboardconfig': {
            'Meta': {'object_name': 'DashboardConfig'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'unique': 'True'}),
            'widgets': ('django.db.models.fields.CharField', [], {'max_length': '4096'})
        },
        'storageadmin.dcontainer': {
            'Meta': {'object_name': 'DContainer'},
            'dimage': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.DImage']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'launch_order': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '1024'}),
            'rockon': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.RockOn']"}),
            'uid': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
        },
        'storageadmin.dcontainerenv': {
            'Meta': {'unique_together': "(('container', 'key'),)", 'object_name': 'DContainerEnv'},
            'container': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.DContainer']"}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '2048', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'val': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'})
        },
        'storageadmin.dcontainerlink': {
            'Meta': {'unique_together': "(('destination', 'name'),)", 'object_name': 'DContainerLink'},
            'destination': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'destination_container'", 'to': "orm['storageadmin.DContainer']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'source': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['storageadmin.DContainer']", 'unique': 'True'})
        },
        'storageadmin.dcustomconfig': {
            'Meta': {'unique_together': "(('rockon', 'key'),)", 'object_name': 'DCustomConfig'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '2048', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'rockon': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.RockOn']"}),
            'val': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'})
        },
        'storageadmin.dimage': {
            'Meta': {'object_name': 'DImage'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'repo': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'tag': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        },
        'storageadmin.disk': {
            'Meta': {'object_name': 'Disk'},
            'btrfs_uuid': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'offline': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'parted': ('django.db.models.fields.BooleanField', [], {}),
            'pool': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Pool']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'serial': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'size': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'smart_available': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'smart_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'smart_options': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'transport': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'vendor': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'})
        },
        'storageadmin.dport': {
            'Meta': {'unique_together': "(('container', 'containerp'),)", 'object_name': 'DPort'},
            'container': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.DContainer']"}),
            'containerp': ('django.db.models.fields.IntegerField', [], {}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'hostp': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'hostp_default': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'protocol': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'}),
            'uiport': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'storageadmin.dvolume': {
            'Meta': {'unique_together': "(('container', 'dest_dir'),)", 'object_name': 'DVolume'},
            'container': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.DContainer']"}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'dest_dir': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'min_size': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'share': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Share']", 'null': 'True'}),
            'uservol': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'storageadmin.emailclient': {
            'Meta': {'object_name': 'EmailClient'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '1024'}),
            'port': ('django.db.models.fields.IntegerField', [], {'default': '587'}),
            'receiver': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'sender': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'smtp_server': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        },
        'storageadmin.group': {
            'Meta': {'object_name': 'Group'},
            'admin': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'gid': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'groupname': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
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
        'storageadmin.netatalkshare': {
            'Meta': {'object_name': 'NetatalkShare'},
            'description': ('django.db.models.fields.CharField', [], {'default': "'afp on rockstor'", 'max_length': '1024'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '4096'}),
            'share': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'netatalkshare'", 'unique': 'True', 'to': "orm['storageadmin.Share']"}),
            'time_machine': ('django.db.models.fields.CharField', [], {'default': "'yes'", 'max_length': '3'})
        },
        'storageadmin.networkinterface': {
            'Meta': {'object_name': 'NetworkInterface'},
            'autoconnect': ('django.db.models.fields.CharField', [], {'max_length': '8', 'null': 'True'}),
            'ctype': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'dname': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'dns_servers': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'dspeed': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'dtype': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'gateway': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ipaddr': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'itype': ('django.db.models.fields.CharField', [], {'default': "'io'", 'max_length': '100'}),
            'mac': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'netmask': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'})
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
            'compression': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mnt_options': ('django.db.models.fields.CharField', [], {'max_length': '4096', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '4096'}),
            'raid': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'size': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'toc': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'})
        },
        'storageadmin.poolbalance': {
            'Meta': {'object_name': 'PoolBalance'},
            'end_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'percent_done': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'pool': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Pool']"}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'started'", 'max_length': '10'}),
            'tid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'null': 'True'})
        },
        'storageadmin.poolscrub': {
            'Meta': {'object_name': 'PoolScrub'},
            'corrected_errors': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'csum_discards': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'csum_errors': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'data_extents_scrubbed': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'end_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kb_scrubbed': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'last_physical': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'malloc_errors': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'no_csum': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'pid': ('django.db.models.fields.IntegerField', [], {}),
            'pool': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Pool']"}),
            'read_errors': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'started'", 'max_length': '10'}),
            'super_errors': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'tree_bytes_scrubbed': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'tree_extents_scrubbed': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'uncorrectable_errors': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'unverified_errors': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'verify_errors': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'storageadmin.posixacls': {
            'Meta': {'object_name': 'PosixACLs'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'perms': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'smb_share': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.SambaShare']"})
        },
        'storageadmin.rockon': {
            'Meta': {'object_name': 'RockOn'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '2048'}),
            'https': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'icon': ('django.db.models.fields.URLField', [], {'max_length': '1024', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'more_info': ('django.db.models.fields.CharField', [], {'max_length': '4096', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '2048'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '2048'}),
            'ui': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '2048'}),
            'volume_add_support': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'website': ('django.db.models.fields.CharField', [], {'max_length': '2048', 'null': 'True'})
        },
        'storageadmin.sambacustomconfig': {
            'Meta': {'object_name': 'SambaCustomConfig'},
            'custom_config': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'smb_share': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.SambaShare']"})
        },
        'storageadmin.sambashare': {
            'Meta': {'object_name': 'SambaShare'},
            'browsable': ('django.db.models.fields.CharField', [], {'default': "'yes'", 'max_length': '3'}),
            'comment': ('django.db.models.fields.CharField', [], {'default': "'foo bar'", 'max_length': '100'}),
            'guest_ok': ('django.db.models.fields.CharField', [], {'default': "'no'", 'max_length': '3'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '4096'}),
            'read_only': ('django.db.models.fields.CharField', [], {'default': "'no'", 'max_length': '3'}),
            'shadow_copy': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'share': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'sambashare'", 'unique': 'True', 'to': "orm['storageadmin.Share']"}),
            'snapshot_prefix': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'})
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
            'compression_algo': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'eusage': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'group': ('django.db.models.fields.CharField', [], {'default': "'root'", 'max_length': '4096'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '4096'}),
            'owner': ('django.db.models.fields.CharField', [], {'default': "'root'", 'max_length': '4096'}),
            'perms': ('django.db.models.fields.CharField', [], {'default': "'755'", 'max_length': '9'}),
            'pool': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Pool']"}),
            'pqgroup': ('django.db.models.fields.CharField', [], {'default': "'-1/-1'", 'max_length': '32'}),
            'qgroup': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'replica': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'rusage': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'size': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'subvol_name': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'toc': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'})
        },
        'storageadmin.smartattribute': {
            'Meta': {'object_name': 'SMARTAttribute'},
            'aid': ('django.db.models.fields.IntegerField', [], {}),
            'atype': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'failed': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'flag': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.SMARTInfo']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'normed_value': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'raw_value': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'threshold': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'updated': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'worst': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'storageadmin.smartcapability': {
            'Meta': {'object_name': 'SMARTCapability'},
            'capabilities': ('django.db.models.fields.CharField', [], {'max_length': '2048'}),
            'flag': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.SMARTInfo']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        },
        'storageadmin.smarterrorlog': {
            'Meta': {'object_name': 'SMARTErrorLog'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.SMARTInfo']"}),
            'line': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'storageadmin.smarterrorlogsummary': {
            'Meta': {'object_name': 'SMARTErrorLogSummary'},
            'details': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'error_num': ('django.db.models.fields.IntegerField', [], {}),
            'etype': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.SMARTInfo']"}),
            'lifetime_hours': ('django.db.models.fields.IntegerField', [], {}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'storageadmin.smartidentity': {
            'Meta': {'object_name': 'SMARTIdentity'},
            'assessment': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'ata_version': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'capacity': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'device_model': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'enabled': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'firmware_version': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_smartdb': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'info': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.SMARTInfo']"}),
            'model_family': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'rotation_rate': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'sata_version': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'scanned_on': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'sector_size': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'serial_number': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'supported': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'world_wide_name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'storageadmin.smartinfo': {
            'Meta': {'object_name': 'SMARTInfo'},
            'disk': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Disk']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'toc': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'storageadmin.smarttestlog': {
            'Meta': {'object_name': 'SMARTTestLog'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.SMARTInfo']"}),
            'lba_of_first_error': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'lifetime_hours': ('django.db.models.fields.IntegerField', [], {}),
            'pct_completed': ('django.db.models.fields.IntegerField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'test_num': ('django.db.models.fields.IntegerField', [], {})
        },
        'storageadmin.smarttestlogdetail': {
            'Meta': {'object_name': 'SMARTTestLogDetail'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.SMARTInfo']"}),
            'line': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'storageadmin.snapshot': {
            'Meta': {'unique_together': "(('share', 'name'),)", 'object_name': 'Snapshot'},
            'eusage': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'qgroup': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'real_name': ('django.db.models.fields.CharField', [], {'default': "'unknownsnap'", 'max_length': '4096'}),
            'rusage': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'share': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Share']"}),
            'size': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'snap_type': ('django.db.models.fields.CharField', [], {'default': "'admin'", 'max_length': '64'}),
            'toc': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
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
        'storageadmin.tlscertificate': {
            'Meta': {'object_name': 'TLSCertificate'},
            'certificate': ('django.db.models.fields.CharField', [], {'max_length': '12288', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '12288', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '1024'})
        },
        'storageadmin.updatesubscription': {
            'Meta': {'object_name': 'UpdateSubscription'},
            'appliance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Appliance']"}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '512'})
        },
        'storageadmin.user': {
            'Meta': {'object_name': 'User'},
            'admin': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'gid': ('django.db.models.fields.IntegerField', [], {'default': '5000'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storageadmin.Group']", 'null': 'True', 'blank': 'True'}),
            'homedir': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'public_key': ('django.db.models.fields.CharField', [], {'max_length': '4096', 'null': 'True', 'blank': 'True'}),
            'shell': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'smb_shares': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'admin_users'", 'null': 'True', 'to': "orm['storageadmin.SambaShare']"}),
            'uid': ('django.db.models.fields.IntegerField', [], {'default': '5000'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'suser'", 'unique': 'True', 'null': 'True', 'to': u"orm['auth.User']"}),
            'username': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '4096'})
        }
    }

    complete_apps = ['storageadmin']