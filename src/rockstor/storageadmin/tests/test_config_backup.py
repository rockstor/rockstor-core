"""
Copyright (c) 2012-2013 RockStor, Inc. <http://rockstor.com>
This file is part of RockStor.
RockStor is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.
RockStor is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
from rest_framework import status
from rest_framework.test import APITestCase

from storageadmin.models import RockOn
from storageadmin.tests.test_api import APITestMixin
from storageadmin.views.config_backup import get_sname, update_rockon_shares, \
    validate_install_config


class ConfigBackupTests(APITestMixin, APITestCase):
    fixtures = [
        'fix2.json'
        # 'test_config_backup_rockons.json'
        ]
    BASE_URL = '/api/config-backup'
    sa_ml = [{'fields':
                  {'status': 'stopped', 'website': 'https://hub.docker.com/r/linuxserver/mariadb/',
                   'volume_add_support': True, 'name': 'MariaDB',
                   'description': 'MariaDB, relational database management system.', 'state': 'installed',
                   'version': '1.0', 'link': '', 'https': False, 'ui': False, 'icon': None,
                   'more_info': '<h4>Important locations</h4><p>Configuration file:<code>/config/custom.cnf</code></p> <p>Databases: <code>/config/databases</code></p> <p>Logs: <code>/config/log/mysql/</code></p>'},
              'model': 'storageadmin.rockon', 'pk': 58},
             {'fields':
                  {'status': 'stopped', 'website': 'https://hub.docker.com/r/linuxserver/smokeping/',
                   'volume_add_support': True, 'name': 'SmokePing',
                   'description': 'SmokePing is a network latency history monitor.', 'state': 'available',
                   'version': '1.0', 'link': 'smokeping/smokeping.cgi', 'https': False, 'ui': True,
                   'icon': None, 'more_info': None}, 'model': 'storageadmin.rockon', 'pk': 59},
             {'fields':
                  {'status': 'exitcode: 137 error: ', 'website': '', 'volume_add_support': True,
                   'name': 'Alpine With AddStorage Single', 'description': 'Alpine test Rock-on.',
                   'state': 'installed', 'version': '1.0', 'link': '', 'https': False, 'ui': False,
                   'icon': None, 'more_info': None}, 'model': 'storageadmin.rockon', 'pk': 73},
             {'fields':
                  {'status': 'stopped', 'website': 'https://emby.media/', 'volume_add_support': True,
                   'name': 'Emby server', 'description': 'Emby media server', 'state': 'installed',
                   'version': '1.0', 'link': '', 'https': False, 'ui': True, 'icon': None,
                   'more_info': '<h4>Adding media to Emby.</h4><p>You can add Shares(with media) to Emby from the settings wizard of this Rock-on. Then, from Emby WebUI, you can update and re-index your library.</p><p> Visit https://hub.docker.com/r/emby/embyserver for description of each option.'},
              'model': 'storageadmin.rockon', 'pk': 74},
             {'fields':
                  {'status': 'exitcode: 137 error: ', 'website': '', 'volume_add_support': True,
                   'name': 'Alpine With AddStorage 2Ports', 'description': 'Alpine test Rock-on.',
                   'state': 'installed', 'version': '1.0', 'link': '', 'https': False, 'ui': True,
                   'icon': None, 'more_info': None},
              'model': 'storageadmin.rockon', 'pk': 75},
             {'fields': {'launch_order': 1, 'rockon': 58, 'uid': None, 'name': 'linuxserver-mariadb', 'dimage': 62},
              'model': 'storageadmin.dcontainer', 'pk': 62},
             {'fields': {'launch_order': 1, 'rockon': 59, 'uid': None, 'name': 'SmokePing', 'dimage': 63},
              'model': 'storageadmin.dcontainer', 'pk': 63},
             {'fields': {'launch_order': 1, 'rockon': 73, 'uid': None, 'name': 'alpinesingle', 'dimage': 76},
              'model': 'storageadmin.dcontainer', 'pk': 78},
             {'fields': {'launch_order': 1, 'rockon': 74, 'uid': None, 'name': 'embyserver', 'dimage': 52},
              'model': 'storageadmin.dcontainer', 'pk': 79},
             {'fields': {'launch_order': 1, 'rockon': 75, 'uid': None, 'name': 'alpine2p1', 'dimage': 76},
              'model': 'storageadmin.dcontainer', 'pk': 80},
             {'fields': {'launch_order': 2, 'rockon': 75, 'uid': None, 'name': 'alpine2p2', 'dimage': 76},
              'model': 'storageadmin.dcontainer', 'pk': 81},
             {'fields':
                 {
                     'description': 'Enter a valid UID to run MariaDB as. It must have full permissions to the share mapped in the previous step.',
                     'container': 62, 'key': 'PUID', 'val': '1000', 'label': 'UID to run MariaDB as.'},
                 'model': 'storageadmin.dcontainerenv', 'pk': 71},
             {'fields':
                 {
                     'description': 'Enter a valid GID to use along with the above UID. It (or the above UID) must have full permissions to the share mapped in the previous step.',
                     'container': 62, 'key': 'PGID', 'val': '1000', 'label': 'GID to run MariaDB as.'},
                 'model': 'storageadmin.dcontainerenv', 'pk': 72},
             {'fields':
                  {'description': 'Enter a root password for the MariaDB server (minimum 4 characters).',
                   'container': 62, 'key': 'MYSQL_ROOT_PASSWORD', 'val': 'PASSWORD',
                   'label': 'Root password.'},
              'model': 'storageadmin.dcontainerenv', 'pk': 73},
             {'fields':
                 {
                     'description': 'Enter a valid UID to run SmokePing as. It must have full permissions to all Shares mapped in the previous step.',
                     'container': 63, 'key': 'PUID', 'val': None, 'label': 'UID to run SmokePing as.'},
                 'model': 'storageadmin.dcontainerenv', 'pk': 74},
             {'fields':
                 {
                     'description': 'Enter a valid GID to use along with the above UID. It(or the above UID) must have full permissions to all Shares mapped in the previous step.',
                     'container': 63, 'key': 'PGID', 'val': None, 'label': 'GID to run SmokePing as.'},
                 'model': 'storageadmin.dcontainerenv', 'pk': 75},
             {'fields': {
                 'description': 'Enter a valid UID of an existing user with permission to media shares to run Emby as.',
                 'container': 79, 'key': 'UID', 'val': '1000', 'label': 'UID'},
                 'model': 'storageadmin.dcontainerenv',
                 'pk': 95},
             {'fields': {
                 'description': 'Enter a valid GID of an existing user with permission to media shares to run Emby as.',
                 'container': 79, 'key': 'GID', 'val': '1000', 'label': 'GID'},
                 'model': 'storageadmin.dcontainerenv',
                 'pk': 96},
             {'fields': {
                 'description': 'Enter a comma-separated list of additional GIDs to run emby as',
                 'container': 79, 'key': 'GIDLIST', 'val': '100', 'label': 'GIDList'},
                 'model': 'storageadmin.dcontainerenv', 'pk': 97},
             {'fields': {
                 'container': 80, 'key': 'alpine2p1', 'val': 'test1'},
                 'model': 'storageadmin.dcontainerlabel', 'pk': 3},
             {'fields': {
                 'container': 78, 'key': 'alpinesingle', 'val': 'test2'},
                 'model': 'storageadmin.dcontainerlabel', 'pk': 4},
             {'fields': {
                 'container': 79, 'key': 'embyserver', 'val': 'test3'},
                 'model': 'storageadmin.dcontainerlabel', 'pk': 5},
             {'fields': {
                 'container': 62, 'key': 'linuxserver-mariadb', 'val': 'test4'},
                 'model': 'storageadmin.dcontainerlabel', 'pk': 6},
             {'fields': {
                 'container': 62,
                 'description': 'Choose a share where the database should be stored. Eg: create a share called mariadb-server1 for this purpose alone. ',
                 'uservol': False, 'share': 3, 'label': 'Data Storage', 'min_size': None,
                 'dest_dir': '/config'}, 'model': 'storageadmin.dvolume', 'pk': 98},
             {'fields': {
                 'container': 63, 'description': 'Choose a Share for SmokePing Configuration Files',
                 'uservol': False, 'share': None, 'label': 'Config Storage', 'min_size': None,
                 'dest_dir': '/config'}, 'model': 'storageadmin.dvolume', 'pk': 99},
             {'fields': {
                 'container': 63, 'description': 'Choose a Share for SmokePing Data Files',
                 'uservol': False, 'share': None, 'label': 'Data location', 'min_size': None,
                 'dest_dir': '/data'}, 'model': 'storageadmin.dvolume', 'pk': 100},
             {'fields': {
                 'container': 79,
                 'description': 'Choose a Share for the Emby Server configuration. Eg: create a Share called emby-config for this purpose alone.',
                 'uservol': False, 'share': 14, 'label': 'Config Storage', 'min_size': None,
                 'dest_dir': '/config'}, 'model': 'storageadmin.dvolume', 'pk': 124},
             {'fields': {
                 'container': 79,
                 'description': 'Choose a Share with media content. Eg: create a Share called emby-media for this purpose alone or use an existing share. It will be available as /media inside Emby.',
                 'uservol': False, 'share': 15, 'label': 'Media Storage', 'min_size': None,
                 'dest_dir': '/media'}, 'model': 'storageadmin.dvolume', 'pk': 125},
             {'fields': {
                 'container': 62, 'description': 'MariaDB port. Suggested default: 3306',
                 'hostp_default': 3306, 'protocol': 'tcp', 'label': 'MariaDB port', 'hostp': 3306,
                 'uiport': False, 'containerp': 3306}, 'model': 'storageadmin.dport', 'pk': 76},
             {'fields': {
                 'container': 63, 'description': 'SmokePing WebUI port. Suggested default: 7878',
                 'hostp_default': 87, 'protocol': 'tcp', 'label': 'WebUI port', 'hostp': 85,
                 'uiport': True, 'containerp': 80}, 'model': 'storageadmin.dport', 'pk': 77},
             {'fields': {
                 'container': 79, 'description': 'Emby Server WebUI port. Suggested default: 8096',
                 'hostp_default': 8096, 'protocol': 'tcp', 'label': 'WebUI port', 'hostp': 8096,
                 'uiport': True, 'containerp': 8096}, 'model': 'storageadmin.dport', 'pk': 108},
             {'fields': {
                 'container': 79, 'description': 'Emby Server HTTPS port. Suggested default: 8920',
                 'hostp_default': 8920, 'protocol': 'tcp', 'label': 'HTTPS port', 'hostp': 8920,
                 'uiport': False, 'containerp': 8920}, 'model': 'storageadmin.dport', 'pk': 109},
             {'fields': {
                 'container': 81, 'description': 'Fake second port. Suggested default: 9100',
                 'hostp_default': 9100, 'protocol': 'tcp', 'label': 'Random port', 'hostp': 9100,
                 'uiport': False, 'containerp': 9100}, 'model': 'storageadmin.dport', 'pk': 110},
             {'fields': {
                 'container': 81, 'description': 'Fake WebUI port. Suggested default: 9000',
                 'hostp_default': 9002, 'protocol': 'tcp', 'label': 'WebUI port', 'hostp': 9001,
                 'uiport': True, 'containerp': 9000}, 'model': 'storageadmin.dport', 'pk': 111},
             {'fields': {
                 'description': '<u>Optional:</u> path to hardware transcoding device (/dev/dri/renderD128). Leave blank if not needed.',
                 'container': 79, 'dev': 'VAAPI', 'val': '', 'label': 'VAAPI device'},
                 'model': 'storageadmin.dcontainerdevice',
                 'pk': 2},
             {'fields': {
                 'group': 'root', 'name': 'home', 'perms': '755', 'pqgroup_rusage': 16, 'eusage': 16,
                 'rusage': 16, 'compression_algo': None, 'qgroup': '0/257', 'replica': False,
                 'pqgroup': '2015/1', 'owner': 'root', 'toc': '2019-10-05T16:50:07.480Z',
                 'subvol_name': 'home', 'size': 7035904, 'pqgroup_eusage': 16, 'pool': 1, 'uuid': None},
                 'model': 'storageadmin.share', 'pk': 1},
             {'fields': {
                 'group': 'root', 'name': 'test_share01', 'perms': '755', 'pqgroup_rusage': 16,
                 'eusage': 16, 'rusage': 16, 'compression_algo': None, 'qgroup': '0/257',
                 'replica': False, 'pqgroup': '2015/1', 'owner': 'root',
                 'toc': '2019-10-05T16:50:08.021Z', 'subvol_name': 'test_share01', 'size': 5242880,
                 'pqgroup_eusage': 16, 'pool': 2, 'uuid': None}, 'model': 'storageadmin.share', 'pk': 2},
             {'fields': {
                 'group': 'root', 'name': 'test_share02', 'perms': '755', 'pqgroup_rusage': 114964,
                 'eusage': 114964, 'rusage': 114964, 'compression_algo': None, 'qgroup': '0/258',
                 'replica': False, 'pqgroup': '2015/2', 'owner': 'root', 'toc': '2019-10-05T16:50:08.121Z',
                 'subvol_name': 'test_share02', 'size': 5242880, 'pqgroup_eusage': 114964, 'pool': 2,
                 'uuid': None}, 'model': 'storageadmin.share', 'pk': 3},
             {'fields': {
                 'group': 'root', 'name': 'test_share03', 'perms': '755', 'pqgroup_rusage': 16,
                 'eusage': 16, 'rusage': 16, 'compression_algo': None, 'qgroup': '0/259',
                 'replica': False, 'pqgroup': '2015/3', 'owner': 'root',
                 'toc': '2019-10-05T16:50:08.229Z', 'subvol_name': 'test_share03', 'size': 5242880,
                 'pqgroup_eusage': 16, 'pool': 2, 'uuid': None}, 'model': 'storageadmin.share', 'pk': 4},
             {'fields': {
                 'group': 'root', 'name': 'test_share04', 'perms': '755', 'pqgroup_rusage': 16,
                 'eusage': 16, 'rusage': 16, 'compression_algo': None, 'qgroup': '0/260', 'replica': False,
                 'pqgroup': '2015/4', 'owner': 'root', 'toc': '2019-10-05T16:50:08.326Z',
                 'subvol_name': 'test_share04', 'size': 5242880, 'pqgroup_eusage': 16, 'pool': 2,
                 'uuid': None}, 'model': 'storageadmin.share', 'pk': 5},
             {'fields': {
                 'group': 'root', 'name': 'test_share05', 'perms': '755', 'pqgroup_rusage': 16,
                 'eusage': 16, 'rusage': 16, 'compression_algo': None, 'qgroup': '0/261',
                 'replica': False, 'pqgroup': '2015/5', 'owner': 'root',
                 'toc': '2019-10-05T16:50:08.424Z', 'subvol_name': 'test_share05', 'size': 5242880,
                 'pqgroup_eusage': 16, 'pool': 2, 'uuid': None}, 'model': 'storageadmin.share', 'pk': 6},
             {'fields': {
                 'group': 'root', 'name': 'test_share06', 'perms': '755', 'pqgroup_rusage': 16,
                 'eusage': 16, 'rusage': 16, 'compression_algo': None, 'qgroup': '0/262', 'replica': False,
                 'pqgroup': '2015/6', 'owner': 'root', 'toc': '2019-10-05T16:50:08.541Z',
                 'subvol_name': 'test_share06', 'size': 5242880, 'pqgroup_eusage': 16, 'pool': 2,
                 'uuid': None}, 'model': 'storageadmin.share', 'pk': 7},
             {'fields': {
                 'group': 'root', 'name': 'test_share07', 'perms': '755', 'pqgroup_rusage': 16,
                 'eusage': 16, 'rusage': 16, 'compression_algo': None, 'qgroup': '0/263',
                 'replica': False, 'pqgroup': '2015/7', 'owner': 'root',
                 'toc': '2019-10-05T16:50:08.650Z', 'subvol_name': 'test_share07', 'size': 5242880,
                 'pqgroup_eusage': 16, 'pool': 2, 'uuid': None}, 'model': 'storageadmin.share', 'pk': 8},
             {'fields': {
                 'group': 'root', 'name': 'test_share08', 'perms': '755', 'pqgroup_rusage': 16,
                 'eusage': 16, 'rusage': 16, 'compression_algo': None, 'qgroup': '0/264', 'replica': False,
                 'pqgroup': '2015/8', 'owner': 'root', 'toc': '2019-10-05T16:50:08.744Z',
                 'subvol_name': 'test_share08', 'size': 5242880, 'pqgroup_eusage': 16, 'pool': 2,
                 'uuid': None}, 'model': 'storageadmin.share', 'pk': 9},
             {'fields': {
                 'group': 'root', 'name': 'test_share09', 'perms': '755', 'pqgroup_rusage': 16,
                 'eusage': 16, 'rusage': 16, 'compression_algo': None, 'qgroup': '0/265',
                 'replica': False, 'pqgroup': '2015/9', 'owner': 'root',
                 'toc': '2019-10-05T16:50:08.856Z', 'subvol_name': 'test_share09', 'size': 5242880,
                 'pqgroup_eusage': 16, 'pool': 2, 'uuid': None}, 'model': 'storageadmin.share',
                 'pk': 10},
             {'fields': {
                 'group': 'root', 'name': 'test_share11', 'perms': '755', 'pqgroup_rusage': 16,
                 'eusage': 16, 'rusage': 16, 'compression_algo': None, 'qgroup': '0/267',
                 'replica': False, 'pqgroup': '2015/10', 'owner': 'root',
                 'toc': '2019-10-05T16:50:08.955Z', 'subvol_name': 'test_share11', 'size': 5242880,
                 'pqgroup_eusage': 16, 'pool': 2, 'uuid': None}, 'model': 'storageadmin.share',
                 'pk': 11},
             {'fields': {
                 'group': 'root', 'name': 'test_share10', 'perms': '755', 'pqgroup_rusage': 16,
                 'eusage': 16, 'rusage': 16, 'compression_algo': None, 'qgroup': '0/266',
                 'replica': False, 'pqgroup': '2015/14', 'owner': 'root',
                 'toc': '2019-10-05T16:50:09.337Z', 'subvol_name': 'test_share10', 'size': 5242880,
                 'pqgroup_eusage': 16, 'pool': 2, 'uuid': None}, 'model': 'storageadmin.share',
                 'pk': 12},
             {'fields': {
                 'group': 'root', 'name': 'rockons_root', 'perms': '755', 'pqgroup_rusage': 3440,
                 'eusage': 3440, 'rusage': 3440, 'compression_algo': 'no', 'qgroup': '0/268',
                 'replica': False, 'pqgroup': '2015/11', 'owner': 'root',
                 'toc': '2019-10-05T16:50:09.077Z', 'subvol_name': 'rockons_root', 'size': 1048576,
                 'pqgroup_eusage': 3440, 'pool': 2, 'uuid': None}, 'model': 'storageadmin.share',
                 'pk': 13},
             {'fields': {
                 'group': 'root', 'name': 'emby-conf', 'perms': '755', 'pqgroup_rusage': 6144,
                 'eusage': 6144, 'rusage': 6144, 'compression_algo': 'no', 'qgroup': '0/274',
                 'replica': False, 'pqgroup': '2015/15', 'owner': 'root',
                 'toc': '2019-10-05T16:50:09.413Z', 'subvol_name': 'emby-conf', 'size': 1048576,
                 'pqgroup_eusage': 6144, 'pool': 2, 'uuid': None}, 'model': 'storageadmin.share',
                 'pk': 14},
             {'fields': {
                 'group': 'root', 'name': 'emby-media', 'perms': '755', 'pqgroup_rusage': 16,
                 'eusage': 16, 'rusage': 16, 'compression_algo': 'no', 'qgroup': '0/275',
                 'replica': False, 'pqgroup': '2015/12', 'owner': 'root',
                 'toc': '2019-10-05T16:50:09.171Z', 'subvol_name': 'emby-media', 'size': 1048576,
                 'pqgroup_eusage': 16, 'pool': 2, 'uuid': None}, 'model': 'storageadmin.share',
                 'pk': 15},
             {'fields': {
                 'group': 'root', 'name': 'next-main', 'perms': '755', 'pqgroup_rusage': 258027,
                 'eusage': 258027, 'rusage': 258027, 'compression_algo': 'no', 'qgroup': '0/298',
                 'replica': False, 'pqgroup': '2015/13', 'owner': 'root',
                 'toc': '2019-10-05T16:50:09.258Z', 'subvol_name': 'next-main', 'size': 1048576,
                 'pqgroup_eusage': 258027, 'pool': 2, 'uuid': None}, 'model': 'storageadmin.share',
                 'pk': 16}
             ]


    @classmethod
    def setUpClass(cls):
        super(ConfigBackupTests, cls).setUpClass()

        # Create RockOn objects as per fixture
        cls.rockon_alpine_single = RockOn(id=73, name="Alpine With AddStorage Single")
        cls.rockon_mariadb = RockOn(id=58, name="MariaDB")
        cls.rockon_alpine_2ports = RockOn(id=75, name="Alpine With AddStorage 2Ports")
        cls.rockon_emby = RockOn(id=74, name="Emby server")

        # TODO: may need to mock os.path.isfile

    @classmethod
    def tearDownClass(cls):
        super(ConfigBackupTests, cls).tearDownClass()

    def test_valid_requests(self):
        # happy path POST
        response = self.client.post(self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # Happy path POST with restore command test restore .... backup with
        # id=1 is created when above post api call is made
        data = {'command': 'restore'}
        response = self.client.post('%s/1' % self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # Happy path DELETE
        response = self.client.delete('%s/1' % self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    # TODO: 'module' object has no attribute 'views'
    #     when attempting to mock uploaded file content.
    # @mock.patch(storageadmin.views.config_backup.ConfigBackup)
    # def test_config_upload_file(self, mock_config_backup):
    #
    #     # happy path POST
    #     # so the following test throws:
    #     # 'FileUpload parse error - none of upload handlers can handle the
    #     # stream'
    #
    #     # we use a SimpleUploadedFile Object to act as our
    #     # ConfigBackup.config_backup (a models.fileField)
    #
    #     # setup fake zip file as models.FileField substitute in ConfigBackup
    #     fake_file = SimpleUploadedFile('file1.txt', b"fake-file-contents",
    #                                    content_type="application/zip")
    #
    #     # TODO: We also need to setup a content_type='text/plain' to test
    #     #     failure when file is not a zip file.
    #
    #     # override "config_backup = models.FileField" in super
    #     class MockConfigBackup(ConfigBackup):
    #         def __init__(self, **kwargs):
    #             self.config_backup = \
    #                 SimpleUploadedFile(self.filename, b"fake-file-contents",
    #                                    content_type="application/zip")
    #
    #         def save(self):
    #             pass
    #
    #     mock_config_backup.objects.get.side_effect = MockConfigBackup
    #
    #
    #     data = {'file-name': 'file1', 'file': 'file1.txt'}
    #     response = self.client.post('%s/file-upload' % self.BASE_URL,
    #                                 data=data)
    #     self.assertEqual(response.status_code,
    #                      status.HTTP_200_OK, msg=response.data)

    def test_get_sname(self):
        range_pks = range(1,17,1)
        expected_snames = ['home', 'test_share01', 'test_share02', 'test_share03', 'test_share04', 'test_share05',
                           'test_share06', 'test_share07', 'test_share08', 'test_share09', 'test_share11',
                           'test_share10', 'rockons_root', 'emby-conf', 'emby-media', 'next-main']

        for pk, sname in zip(range_pks, expected_snames):
            returned = get_sname(self.sa_ml, pk)
            self.assertEqual(
                returned,
                sname,
                msg="Un-expected get_sname() result:\n "
                "returned = {}.\n "
                "expected = {}.".format(returned, sname),
            )

    def test_get_sname_invalid(self):
        pass

    #@mock.patch("storageadmin.views.config_backup.RockOn.objects")
    # def test_validate_rockons(self):
    #     # mock_rockon.filter.return_value = mock_rockon
    #     # mock_rockon.exists.return_value = False
    #     expected = {73: {'rname': 'Alpine With AddStorage Single', 'new_rid': 73},
    #                 58: {'rname': 'MariaDB', 'new_rid': 58},
    #                 75: {'rname': 'Alpine With AddStorage 2Ports', 'new_rid': 75},
    #                 74: {'rname': 'Emby server', 'new_rid': 74}}
    #
    #     returned = validate_rockons(self.sa_ml)
    #     self.assertEqual(
    #         returned,
    #         expected,
    #         msg="Un-expected validate_rockons() result:\n "
    #             "returned = {}.\n "
    #             "expected = {}.".format(returned, expected),
    #     )

    def test_validate_rockons_invalid(self):
        pass

    def test_update_rockon_shares(self):
        cid = [78]
        rid = [73]
        expected_rockons = [
            {73: {'rname': 'Alpine With AddStorage Single', 'new_rid': 73, 'containers': [78], 'shares': {}},
             58: {'rname': 'MariaDB', 'new_rid': 58, 'containers': [62], 'shares': {}},
             75: {'rname': 'Alpine With AddStorage 2Ports', 'new_rid': 75, 'containers': [80, 81], 'shares': {}},
             74: {'rname': 'Emby server', 'new_rid': 74, 'containers': [79], 'shares': {}}}
            ]

        cid.append(62)
        rid.append(58)
        expected_rockons.append(
            {73: {'rname': 'Alpine With AddStorage Single', 'new_rid': 73, 'containers': [78], 'shares': {}},
             58: {'rname': 'MariaDB', 'new_rid': 58, 'containers': [62], 'shares': {'test_share02': '/config'}},
             75: {'rname': 'Alpine With AddStorage 2Ports', 'new_rid': 75, 'containers': [80, 81], 'shares': {}},
             74: {'rname': 'Emby server', 'new_rid': 74, 'containers': [79], 'shares': {}}}
        )

        cid.append(80)
        rid.append(75)
        expected_rockons.append(
            {73: {'rname': 'Alpine With AddStorage Single', 'new_rid': 73, 'containers': [78], 'shares': {}},
             58: {'rname': 'MariaDB', 'new_rid': 58, 'containers': [62], 'shares': {}},
             75: {'rname': 'Alpine With AddStorage 2Ports', 'new_rid': 75, 'containers': [80, 81], 'shares': {}},
             74: {'rname': 'Emby server', 'new_rid': 74, 'containers': [79], 'shares': {}}}
        )

        cid.append(81)
        rid.append(75)
        expected_rockons.append(
            {73: {'rname': 'Alpine With AddStorage Single', 'new_rid': 73, 'containers': [78], 'shares': {}},
             58: {'rname': 'MariaDB', 'new_rid': 58, 'containers': [62], 'shares': {}},
             75: {'rname': 'Alpine With AddStorage 2Ports', 'new_rid': 75, 'containers': [80, 81], 'shares': {}},
             74: {'rname': 'Emby server', 'new_rid': 74, 'containers': [79], 'shares': {}}}
        )

        cid.append(79)
        rid.append(74)
        expected_rockons.append(
            {73: {'rname': 'Alpine With AddStorage Single', 'new_rid': 73, 'containers': [78], 'shares': {}},
             58: {'rname': 'MariaDB', 'new_rid': 58, 'containers': [62], 'shares': {}},
             75: {'rname': 'Alpine With AddStorage 2Ports', 'new_rid': 75, 'containers': [80, 81], 'shares': {}},
             74: {'rname': 'Emby server', 'new_rid': 74, 'containers': [79],
                  'shares': {'emby-media': '/media', 'emby-conf': '/config'}}}
        )

        for c, r, out in zip(cid, rid, expected_rockons):
            rockons = {
                73: {'rname': 'Alpine With AddStorage Single', 'new_rid': 73, 'containers': [78], 'shares': {}},
                58: {'rname': 'MariaDB', 'new_rid': 58, 'containers': [62], 'shares': {}},
                75: {'rname': 'Alpine With AddStorage 2Ports', 'new_rid': 75, 'containers': [80, 81], 'shares': {}},
                74: {'rname': 'Emby server', 'new_rid': 74, 'containers': [79], 'shares': {}}}
            expected = out
            update_rockon_shares(c, self.sa_ml, r, rockons)
            self.assertEqual(
                rockons,
                expected,
                msg="Un-expected update_rockon_shares() result:\n "
                "returned = {}.\n "
                "expected = {}.".format(rockons, expected),
            )

    def test_validate_install_config(self):
        rid = [73]
        out = [{73: {'rname': 'Alpine With AddStorage Single', 'cc': {}, 'devices': {}, 'new_rid': 73,
                     'environment': {}, 'shares': {}, 'ports': {}, 'containers': [78]},
                58: {'rname': 'MariaDB', 'new_rid': 58}, 75: {'rname': 'Alpine With AddStorage 2Ports', 'new_rid': 75},
                74: {'rname': 'Emby server', 'new_rid': 74}}
               ]

        rid.append(58)
        out.append({73: {'rname': 'Alpine With AddStorage Single', 'new_rid': 73},
                    58: {'rname': 'MariaDB', 'cc': {}, 'devices': {}, 'new_rid': 58,
                         'environment': {'MYSQL_ROOT_PASSWORD': 'PASSWORD', 'PUID': '1000', 'PGID': '1000'},
                         'shares': {'test_share02': '/config'}, 'ports': {3306: 3306}, 'containers': [62]},
                    75: {'rname': 'Alpine With AddStorage 2Ports', 'new_rid': 75},
                    74: {'rname': 'Emby server', 'new_rid': 74}}
                   )

        rid.append(75)
        out.append(
            {73: {'rname': 'Alpine With AddStorage Single', 'new_rid': 73},
             58: {'rname': 'MariaDB', 'new_rid': 58},
             75: {'rname': 'Alpine With AddStorage 2Ports', 'cc': {}, 'devices': {}, 'new_rid': 75, 'environment': {},
                  'shares': {}, 'ports': {9001: 9000, 9100: 9100}, 'containers': [80, 81]},
             74: {'rname': 'Emby server', 'new_rid': 74}}
            )

        rid.append(74)
        out.append(
            {73: {'rname': 'Alpine With AddStorage Single', 'new_rid': 73},
             58: {'rname': 'MariaDB', 'new_rid': 58},
             75: {'rname': 'Alpine With AddStorage 2Ports', 'new_rid': 75},
             74: {'rname': 'Emby server', 'cc': {}, 'devices': {'VAAPI': ''}, 'new_rid': 74,
                  'environment': {'GID': '1000', 'UID': '1000', 'GIDLIST': '100'},
                  'shares': {'emby-media': '/media', 'emby-conf': '/config'}, 'ports': {8096: 8096, 8920: 8920},
                  'containers': [79]}}
            )

        for r,o in zip(rid, out):
            rockons = {73: {'rname': 'Alpine With AddStorage Single', 'new_rid': 73},
                       58: {'rname': 'MariaDB', 'new_rid': 58},
                       75: {'rname': 'Alpine With AddStorage 2Ports', 'new_rid': 75},
                       74: {'rname': 'Emby server', 'new_rid': 74}}
            validate_install_config(self.sa_ml, r, rockons)
            self.assertEqual(
                rockons,
                o,
                msg="Un-expected update_rockon_shares() result:\n "
                "returned = {}.\n "
                "expected = {}.".format(rockons, o),
            )
