# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
from django.conf import settings
import storageadmin.models.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        migrations.swappable_dependency(settings.OAUTH2_PROVIDER_APPLICATION_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AdvancedNFSExport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('export_str', models.CharField(max_length=4096)),
            ],
        ),
        migrations.CreateModel(
            name='APIKeys',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.CharField(unique=True, max_length=8)),
                ('key', models.CharField(unique=True, max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='Appliance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', models.CharField(unique=True, max_length=64)),
                ('ip', models.CharField(unique=True, max_length=4096)),
                ('current_appliance', models.BooleanField(default=False)),
                ('hostname', models.CharField(default=b'Rockstor', max_length=128)),
                ('mgmt_port', models.IntegerField(default=443)),
                ('client_id', models.CharField(max_length=100, null=True)),
                ('client_secret', models.CharField(max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='BondConnection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, null=True)),
                ('config', models.CharField(max_length=2048, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ConfigBackup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('filename', models.CharField(max_length=64)),
                ('md5sum', models.CharField(max_length=32, null=True)),
                ('size', models.IntegerField(null=True)),
                ('config_backup', models.FileField(null=True, upload_to=b'config-backups')),
            ],
        ),
        migrations.CreateModel(
            name='ContainerOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=1024)),
                ('val', models.CharField(max_length=1024, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='DashboardConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('widgets', models.CharField(max_length=4096)),
            ],
        ),
        migrations.CreateModel(
            name='DContainer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=1024)),
                ('launch_order', models.IntegerField(default=1)),
                ('uid', models.IntegerField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='DContainerEnv',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=1024)),
                ('val', models.CharField(max_length=1024, null=True)),
                ('description', models.CharField(max_length=2048, null=True)),
                ('label', models.CharField(max_length=64, null=True)),
                ('container', models.ForeignKey(to='storageadmin.DContainer')),
            ],
        ),
        migrations.CreateModel(
            name='DContainerLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, null=True)),
                ('destination', models.ForeignKey(related_name='destination_container', to='storageadmin.DContainer')),
                ('source', models.OneToOneField(to='storageadmin.DContainer')),
            ],
        ),
        migrations.CreateModel(
            name='DCustomConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=1024)),
                ('val', models.CharField(max_length=1024, null=True)),
                ('description', models.CharField(max_length=2048, null=True)),
                ('label', models.CharField(max_length=64, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='DImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=1024)),
                ('tag', models.CharField(max_length=1024)),
                ('repo', models.CharField(max_length=1024)),
            ],
        ),
        migrations.CreateModel(
            name='Disk',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=128)),
                ('size', models.BigIntegerField(default=0)),
                ('offline', models.BooleanField(default=False)),
                ('parted', models.BooleanField()),
                ('btrfs_uuid', models.CharField(max_length=1024, null=True)),
                ('model', models.CharField(max_length=1024, null=True)),
                ('serial', models.CharField(max_length=1024, null=True)),
                ('transport', models.CharField(max_length=1024, null=True)),
                ('vendor', models.CharField(max_length=1024, null=True)),
                ('smart_available', models.BooleanField(default=False)),
                ('smart_enabled', models.BooleanField(default=False)),
                ('smart_options', models.CharField(max_length=64, null=True)),
                ('role', models.CharField(max_length=256, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='DPort',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=1024, null=True)),
                ('hostp', models.IntegerField(unique=True)),
                ('hostp_default', models.IntegerField(null=True)),
                ('containerp', models.IntegerField()),
                ('protocol', models.CharField(max_length=32, null=True)),
                ('uiport', models.BooleanField(default=False)),
                ('label', models.CharField(max_length=1024, null=True)),
                ('container', models.ForeignKey(to='storageadmin.DContainer')),
            ],
        ),
        migrations.CreateModel(
            name='DVolume',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dest_dir', models.CharField(max_length=1024)),
                ('uservol', models.BooleanField(default=False)),
                ('description', models.CharField(max_length=1024, null=True)),
                ('min_size', models.IntegerField(null=True)),
                ('label', models.CharField(max_length=1024, null=True)),
                ('container', models.ForeignKey(to='storageadmin.DContainer')),
            ],
        ),
        migrations.CreateModel(
            name='EmailClient',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('smtp_server', models.CharField(max_length=1024)),
                ('port', models.IntegerField(default=587)),
                ('name', models.CharField(unique=True, max_length=1024)),
                ('sender', models.CharField(max_length=1024)),
                ('username', models.CharField(max_length=1024)),
                ('receiver', models.CharField(max_length=1024)),
            ],
        ),
        migrations.CreateModel(
            name='EthernetConnection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('mac', models.CharField(max_length=64, null=True)),
                ('cloned_mac', models.CharField(max_length=64, null=True)),
                ('mtu', models.CharField(max_length=64, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('gid', models.IntegerField(unique=True)),
                ('groupname', models.CharField(max_length=1024, null=True)),
                ('admin', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='InstalledPlugin',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('install_date', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='IscsiTarget',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tid', models.IntegerField(unique=True)),
                ('tname', models.CharField(unique=True, max_length=128)),
                ('dev_name', models.CharField(unique=True, max_length=128)),
                ('dev_size', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='NetatalkShare',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('path', models.CharField(unique=True, max_length=4096)),
                ('description', models.CharField(default=b'afp on rockstor', max_length=1024)),
                ('time_machine', models.CharField(default=b'yes', max_length=3, choices=[(b'yes', b'yes'), (b'no', b'no')])),
            ],
        ),
        migrations.CreateModel(
            name='NetworkConnection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256, null=True)),
                ('uuid', models.CharField(unique=True, max_length=256)),
                ('state', models.CharField(max_length=64, null=True)),
                ('autoconnect', models.BooleanField(default=True)),
                ('ipv4_method', models.CharField(max_length=64, null=True)),
                ('ipv4_addresses', models.CharField(max_length=1024, null=True)),
                ('ipv4_gw', models.CharField(max_length=64, null=True)),
                ('ipv4_dns', models.CharField(max_length=256, null=True)),
                ('ipv4_dns_search', models.CharField(max_length=256, null=True)),
                ('ipv6_method', models.CharField(max_length=1024, null=True)),
                ('ipv6_addresses', models.CharField(max_length=1024, null=True)),
                ('ipv6_gw', models.CharField(max_length=64, null=True)),
                ('ipv6_dns', models.CharField(max_length=256, null=True)),
                ('ipv6_dns_search', models.CharField(max_length=256, null=True)),
                ('master', models.ForeignKey(to='storageadmin.NetworkConnection', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='NetworkDevice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=256)),
                ('dtype', models.CharField(max_length=100, null=True)),
                ('mac', models.CharField(max_length=100, null=True)),
                ('state', models.CharField(max_length=64, null=True)),
                ('mtu', models.CharField(max_length=64, null=True)),
                ('connection', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='storageadmin.NetworkConnection', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='NFSExport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('mount', models.CharField(max_length=4096)),
            ],
        ),
        migrations.CreateModel(
            name='NFSExportGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('host_str', models.CharField(max_length=4096, validators=[storageadmin.models.validators.validate_nfs_host_str])),
                ('editable', models.CharField(default=b'rw', max_length=2, choices=[(b'ro', b'ro'), (b'rw', b'rw')], validators=[storageadmin.models.validators.validate_nfs_modify_str])),
                ('syncable', models.CharField(default=b'async', max_length=5, choices=[(b'async', b'async'), (b'sync', b'sync')], validators=[storageadmin.models.validators.validate_nfs_sync_choice])),
                ('mount_security', models.CharField(default=b'insecure', max_length=8, choices=[(b'secure', b'secure'), (b'insecure', b'insecure')])),
                ('nohide', models.BooleanField(default=False)),
                ('enabled', models.BooleanField(default=True)),
                ('admin_host', models.CharField(max_length=1024, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='OauthApp',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=128)),
                ('application', models.OneToOneField(to=settings.OAUTH2_PROVIDER_APPLICATION_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Pincard',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.IntegerField()),
                ('pin_number', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(24)])),
                ('pin_code', models.CharField(max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name='Plugin',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=4096)),
                ('display_name', models.CharField(default=b'', unique=True, max_length=4096)),
                ('description', models.CharField(default=b'', max_length=4096)),
                ('css_file_name', models.CharField(max_length=4096)),
                ('js_file_name', models.CharField(max_length=4096)),
                ('key', models.CharField(unique=True, max_length=4096)),
            ],
        ),
        migrations.CreateModel(
            name='Pool',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=4096)),
                ('uuid', models.CharField(max_length=100, null=True)),
                ('size', models.BigIntegerField(default=0)),
                ('raid', models.CharField(max_length=10)),
                ('toc', models.DateTimeField(auto_now=True)),
                ('compression', models.CharField(max_length=256, null=True)),
                ('mnt_options', models.CharField(max_length=4096, null=True)),
                ('role', models.CharField(max_length=256, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PoolBalance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.CharField(default=b'started', max_length=10)),
                ('tid', models.CharField(max_length=36, null=True)),
                ('message', models.CharField(max_length=1024, null=True)),
                ('start_time', models.DateTimeField(auto_now=True)),
                ('end_time', models.DateTimeField(null=True)),
                ('percent_done', models.IntegerField(default=0)),
                ('pool', models.ForeignKey(to='storageadmin.Pool')),
            ],
        ),
        migrations.CreateModel(
            name='PoolScrub',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.CharField(default=b'started', max_length=10)),
                ('pid', models.IntegerField()),
                ('start_time', models.DateTimeField(auto_now=True)),
                ('end_time', models.DateTimeField(null=True)),
                ('kb_scrubbed', models.BigIntegerField(null=True)),
                ('data_extents_scrubbed', models.BigIntegerField(default=0)),
                ('tree_extents_scrubbed', models.BigIntegerField(default=0)),
                ('tree_bytes_scrubbed', models.BigIntegerField(default=0)),
                ('read_errors', models.IntegerField(default=0)),
                ('csum_errors', models.IntegerField(default=0)),
                ('verify_errors', models.IntegerField(default=0)),
                ('no_csum', models.IntegerField(default=0)),
                ('csum_discards', models.IntegerField(default=0)),
                ('super_errors', models.IntegerField(default=0)),
                ('malloc_errors', models.IntegerField(default=0)),
                ('uncorrectable_errors', models.IntegerField(default=0)),
                ('unverified_errors', models.IntegerField(default=0)),
                ('corrected_errors', models.IntegerField(default=0)),
                ('last_physical', models.BigIntegerField(default=0)),
                ('pool', models.ForeignKey(to='storageadmin.Pool')),
            ],
        ),
        migrations.CreateModel(
            name='PosixACLs',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('owner', models.CharField(max_length=5, choices=[(b'user', b'user'), (b'group', b'group'), (b'other', b'other')])),
                ('perms', models.CharField(max_length=3, choices=[(b'r', b'r'), (b'w', b'w'), (b'x', b'x'), (b'rw', b'rw'), (b'rx', b'rx'), (b'wx', b'wx'), (b'rwx', b'rwx')])),
            ],
        ),
        migrations.CreateModel(
            name='RockOn',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=1024)),
                ('description', models.CharField(max_length=2048)),
                ('version', models.CharField(max_length=2048)),
                ('state', models.CharField(max_length=2048)),
                ('status', models.CharField(max_length=2048)),
                ('link', models.CharField(max_length=1024, null=True)),
                ('website', models.CharField(max_length=2048, null=True)),
                ('https', models.BooleanField(default=False)),
                ('icon', models.URLField(max_length=1024, null=True)),
                ('ui', models.BooleanField(default=False)),
                ('volume_add_support', models.BooleanField(default=False)),
                ('more_info', models.CharField(max_length=4096, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='SambaCustomConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('custom_config', models.CharField(max_length=1024, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='SambaShare',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('path', models.CharField(unique=True, max_length=4096)),
                ('comment', models.CharField(default=b'foo bar', max_length=100)),
                ('browsable', models.CharField(default=b'yes', max_length=3, choices=[(b'yes', b'yes'), (b'no', b'no')])),
                ('read_only', models.CharField(default=b'no', max_length=3, choices=[(b'yes', b'yes'), (b'no', b'no')])),
                ('guest_ok', models.CharField(default=b'no', max_length=3, choices=[(b'yes', b'yes'), (b'no', b'no')])),
                ('shadow_copy', models.BooleanField(default=False)),
                ('snapshot_prefix', models.CharField(max_length=128, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Setup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('setup_user', models.BooleanField(default=False)),
                ('setup_system', models.BooleanField(default=False)),
                ('setup_disks', models.BooleanField(default=False)),
                ('setup_network', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='SFTP',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('editable', models.CharField(default=b'ro', max_length=2, choices=[(b'ro', b'ro'), (b'rw', b'rw')])),
            ],
        ),
        migrations.CreateModel(
            name='Share',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('qgroup', models.CharField(max_length=100)),
                ('pqgroup', models.CharField(default=b'-1/-1', max_length=32)),
                ('name', models.CharField(unique=True, max_length=4096)),
                ('uuid', models.CharField(max_length=100, null=True)),
                ('size', models.BigIntegerField(default=0)),
                ('owner', models.CharField(default=b'root', max_length=4096)),
                ('group', models.CharField(default=b'root', max_length=4096)),
                ('perms', models.CharField(default=b'755', max_length=9)),
                ('toc', models.DateTimeField(auto_now=True)),
                ('subvol_name', models.CharField(max_length=4096)),
                ('replica', models.BooleanField(default=False)),
                ('compression_algo', models.CharField(max_length=1024, null=True)),
                ('rusage', models.BigIntegerField(default=0)),
                ('eusage', models.BigIntegerField(default=0)),
                ('pool', models.ForeignKey(to='storageadmin.Pool')),
            ],
        ),
        migrations.CreateModel(
            name='SMARTAttribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('aid', models.IntegerField()),
                ('name', models.CharField(max_length=256)),
                ('flag', models.CharField(max_length=64)),
                ('normed_value', models.IntegerField(default=0)),
                ('worst', models.IntegerField(default=0)),
                ('threshold', models.IntegerField(default=0)),
                ('atype', models.CharField(max_length=64)),
                ('raw_value', models.CharField(max_length=256)),
                ('updated', models.CharField(max_length=64)),
                ('failed', models.CharField(max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name='SMARTCapability',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=1024)),
                ('flag', models.CharField(max_length=64)),
                ('capabilities', models.CharField(max_length=2048)),
            ],
        ),
        migrations.CreateModel(
            name='SMARTErrorLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('line', models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='SMARTErrorLogSummary',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('error_num', models.IntegerField()),
                ('lifetime_hours', models.IntegerField()),
                ('state', models.CharField(max_length=64)),
                ('etype', models.CharField(max_length=256)),
                ('details', models.CharField(max_length=1024)),
            ],
        ),
        migrations.CreateModel(
            name='SMARTIdentity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('model_family', models.CharField(max_length=64, verbose_name=b'Model Family')),
                ('device_model', models.CharField(max_length=64, verbose_name=b'Device Model')),
                ('serial_number', models.CharField(max_length=64, verbose_name=b'Serial Number')),
                ('world_wide_name', models.CharField(max_length=64, verbose_name=b'World Wide Name')),
                ('firmware_version', models.CharField(max_length=64, verbose_name=b'Firmware Version')),
                ('capacity', models.CharField(max_length=64, verbose_name=b'Capacity')),
                ('sector_size', models.CharField(max_length=64, verbose_name=b'Sector Size')),
                ('rotation_rate', models.CharField(max_length=64, verbose_name=b'Rotation Rate')),
                ('in_smartdb', models.CharField(max_length=64, verbose_name=b'In Smartctl Database')),
                ('ata_version', models.CharField(max_length=64, verbose_name=b'ATA Version')),
                ('sata_version', models.CharField(max_length=64, verbose_name=b'SATA Version')),
                ('scanned_on', models.CharField(max_length=64, verbose_name=b'Scanned on')),
                ('supported', models.CharField(max_length=64, verbose_name=b'SMART Supported')),
                ('enabled', models.CharField(max_length=64, verbose_name=b'SMART Enabled')),
                ('version', models.CharField(max_length=64, verbose_name=b'Smartctl Version')),
                ('assessment', models.CharField(max_length=64, verbose_name=b'Overall Health Self-Assessment Test')),
            ],
        ),
        migrations.CreateModel(
            name='SMARTInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('toc', models.DateTimeField(auto_now=True)),
                ('disk', models.ForeignKey(to='storageadmin.Disk')),
            ],
        ),
        migrations.CreateModel(
            name='SMARTTestLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('test_num', models.IntegerField()),
                ('description', models.CharField(max_length=64)),
                ('status', models.CharField(max_length=256)),
                ('pct_completed', models.IntegerField()),
                ('lifetime_hours', models.IntegerField()),
                ('lba_of_first_error', models.CharField(max_length=1024)),
                ('info', models.ForeignKey(to='storageadmin.SMARTInfo')),
            ],
        ),
        migrations.CreateModel(
            name='SMARTTestLogDetail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('line', models.CharField(max_length=128)),
                ('info', models.ForeignKey(to='storageadmin.SMARTInfo')),
            ],
        ),
        migrations.CreateModel(
            name='Snapshot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=4096)),
                ('real_name', models.CharField(default=b'unknownsnap', max_length=4096)),
                ('writable', models.BooleanField(default=False)),
                ('size', models.BigIntegerField(default=0)),
                ('toc', models.DateTimeField(auto_now_add=True)),
                ('qgroup', models.CharField(max_length=100)),
                ('uvisible', models.BooleanField(default=False)),
                ('snap_type', models.CharField(default=b'admin', max_length=64)),
                ('rusage', models.BigIntegerField(default=0)),
                ('eusage', models.BigIntegerField(default=0)),
                ('share', models.ForeignKey(to='storageadmin.Share')),
            ],
        ),
        migrations.CreateModel(
            name='SupportCase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('notes', models.TextField()),
                ('zipped_log', models.CharField(max_length=128)),
                ('status', models.CharField(max_length=9, choices=[(b'created', b'created'), (b'submitted', b'submitted'), (b'resolved', b'resolved')])),
                ('case_type', models.CharField(max_length=6, choices=[(b'auto', b'auto'), (b'manual', b'manual')])),
            ],
        ),
        migrations.CreateModel(
            name='TeamConnection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, null=True)),
                ('config', models.CharField(max_length=2048, null=True)),
                ('connection', models.ForeignKey(to='storageadmin.NetworkConnection', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TLSCertificate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=1024)),
                ('certificate', models.CharField(max_length=12288, null=True)),
                ('key', models.CharField(max_length=12288, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='UpdateSubscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=64)),
                ('description', models.CharField(max_length=128)),
                ('url', models.CharField(max_length=512)),
                ('password', models.CharField(max_length=64, null=True)),
                ('status', models.CharField(max_length=64)),
                ('appliance', models.ForeignKey(to='storageadmin.Appliance')),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('username', models.CharField(default=b'', unique=True, max_length=4096)),
                ('uid', models.IntegerField(default=5000)),
                ('gid', models.IntegerField(default=5000)),
                ('public_key', models.CharField(max_length=4096, null=True, blank=True)),
                ('shell', models.CharField(max_length=1024, null=True)),
                ('homedir', models.CharField(max_length=1024, null=True)),
                ('email', models.CharField(blank=True, max_length=1024, null=True, validators=[django.core.validators.EmailValidator()])),
                ('admin', models.BooleanField(default=True)),
                ('group', models.ForeignKey(blank=True, to='storageadmin.Group', null=True)),
                ('smb_shares', models.ManyToManyField(related_name='admin_users', null=True, to='storageadmin.SambaShare')),
                ('user', models.OneToOneField(related_name='suser', null=True, blank=True, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='smartidentity',
            name='info',
            field=models.ForeignKey(to='storageadmin.SMARTInfo'),
        ),
        migrations.AddField(
            model_name='smarterrorlogsummary',
            name='info',
            field=models.ForeignKey(to='storageadmin.SMARTInfo'),
        ),
        migrations.AddField(
            model_name='smarterrorlog',
            name='info',
            field=models.ForeignKey(to='storageadmin.SMARTInfo'),
        ),
        migrations.AddField(
            model_name='smartcapability',
            name='info',
            field=models.ForeignKey(to='storageadmin.SMARTInfo'),
        ),
        migrations.AddField(
            model_name='smartattribute',
            name='info',
            field=models.ForeignKey(to='storageadmin.SMARTInfo'),
        ),
        migrations.AddField(
            model_name='sftp',
            name='share',
            field=models.OneToOneField(to='storageadmin.Share'),
        ),
        migrations.AddField(
            model_name='sambashare',
            name='share',
            field=models.OneToOneField(related_name='sambashare', to='storageadmin.Share'),
        ),
        migrations.AddField(
            model_name='sambacustomconfig',
            name='smb_share',
            field=models.ForeignKey(to='storageadmin.SambaShare'),
        ),
        migrations.AddField(
            model_name='posixacls',
            name='smb_share',
            field=models.ForeignKey(to='storageadmin.SambaShare'),
        ),
        migrations.AlterUniqueTogether(
            name='pincard',
            unique_together=set([('user', 'pin_number')]),
        ),
        migrations.AddField(
            model_name='oauthapp',
            name='user',
            field=models.ForeignKey(to='storageadmin.User'),
        ),
        migrations.AddField(
            model_name='nfsexport',
            name='export_group',
            field=models.ForeignKey(to='storageadmin.NFSExportGroup'),
        ),
        migrations.AddField(
            model_name='nfsexport',
            name='share',
            field=models.ForeignKey(to='storageadmin.Share'),
        ),
        migrations.AddField(
            model_name='netatalkshare',
            name='share',
            field=models.OneToOneField(related_name='netatalkshare', to='storageadmin.Share'),
        ),
        migrations.AddField(
            model_name='iscsitarget',
            name='share',
            field=models.ForeignKey(to='storageadmin.Share'),
        ),
        migrations.AddField(
            model_name='installedplugin',
            name='plugin_meta',
            field=models.ForeignKey(to='storageadmin.Plugin'),
        ),
        migrations.AddField(
            model_name='ethernetconnection',
            name='connection',
            field=models.ForeignKey(to='storageadmin.NetworkConnection', null=True),
        ),
        migrations.AddField(
            model_name='dvolume',
            name='share',
            field=models.ForeignKey(to='storageadmin.Share', null=True),
        ),
        migrations.AddField(
            model_name='disk',
            name='pool',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='storageadmin.Pool', null=True),
        ),
        migrations.AddField(
            model_name='dcustomconfig',
            name='rockon',
            field=models.ForeignKey(to='storageadmin.RockOn'),
        ),
        migrations.AddField(
            model_name='dcontainer',
            name='dimage',
            field=models.ForeignKey(to='storageadmin.DImage'),
        ),
        migrations.AddField(
            model_name='dcontainer',
            name='rockon',
            field=models.ForeignKey(to='storageadmin.RockOn'),
        ),
        migrations.AddField(
            model_name='dashboardconfig',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, unique=True),
        ),
        migrations.AddField(
            model_name='containeroption',
            name='container',
            field=models.ForeignKey(to='storageadmin.DContainer'),
        ),
        migrations.AddField(
            model_name='bondconnection',
            name='connection',
            field=models.ForeignKey(to='storageadmin.NetworkConnection', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='snapshot',
            unique_together=set([('share', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='dvolume',
            unique_together=set([('container', 'dest_dir')]),
        ),
        migrations.AlterUniqueTogether(
            name='dport',
            unique_together=set([('container', 'containerp')]),
        ),
        migrations.AlterUniqueTogether(
            name='dcustomconfig',
            unique_together=set([('rockon', 'key')]),
        ),
        migrations.AlterUniqueTogether(
            name='dcontainerlink',
            unique_together=set([('destination', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='dcontainerenv',
            unique_together=set([('container', 'key')]),
        ),
    ]
