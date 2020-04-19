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
from mock import patch
from storageadmin.tests.test_api import APITestMixin


class CommandTests(APITestMixin, APITestCase):
    fixtures = ['fix5.json']
    BASE_URL = '/api/commands'

    @classmethod
    def setUpClass(cls):
        super(CommandTests, cls).setUpClass()

        cls.patch_get_pool_info = patch(
            'fs.btrfs.get_pool_info')
        cls.mock_get_pool_info = cls.patch_get_pool_info.start()
        cls.mock_get_pool_info.return_value = {'disks': [], 'label': 'pool2'}

        cls.patch_pool_raid = patch('storageadmin.views.command.pool_raid')
        cls.mock_pool_raid = cls.patch_pool_raid.start()

        cls.patch_mount_share = patch('storageadmin.views.command.mount_share')
        cls.mock_mount_share = cls.patch_mount_share.start()
        cls.mock_mount_share.return_value = True

        cls.patch_mount_root = patch('storageadmin.views.command.mount_root')
        cls.mock_mount_root = cls.patch_mount_root.start()
        cls.mock_mount_root.return_value = 'dir/poolname'

        cls.patch_mount_snap = patch('storageadmin.views.command.mount_snap')
        cls.mock_mount_snap = cls.patch_mount_snap.start()
        cls.mock_mount_snap.return_value = True

        cls.patch_update_run = patch('storageadmin.views.command.update_run')
        cls.mock_update_run = cls.patch_update_run.start()

        cls.patch_update_check = patch(
            'storageadmin.views.command.rockstor_pkg_update_check')
        cls.mock_update_check = cls.patch_update_check.start()
        cls.mock_update_check.return_value = 1, 1, 1

        cls.patch_system_shutdown = patch(
            'storageadmin.views.command.system_shutdown')
        cls.mock_system_shutdown = cls.patch_system_shutdown.start()

        cls.patch_system_reboot = patch(
            'storageadmin.views.command.system_reboot')
        cls.mock_system_reboot = cls.patch_system_reboot.start()

        cls.patch_import_shares = patch(
            'storageadmin.views.command.import_shares')
        cls.mock_import_shares = cls.patch_import_shares.start()

        cls.patch_import_snapshots = patch(
            'storageadmin.views.command.import_snapshots')
        cls.mock_import_snapshots = cls.patch_import_snapshots.start()

    @classmethod
    def tearDownClass(cls):
        super(CommandTests, cls).tearDownClass()

    def test_bootstrap_command(self):
        # bootstrap command
        response = self.client.post('{}/bootstrap'.format(self.BASE_URL))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_utcnow_command(self):
        # utcnow command
        response = self.client.post('{}/utcnow'.format(self.BASE_URL))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_uptime_command(self):
        # uptime command
        response = self.client.post('{}/uptime'.format(self.BASE_URL))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_kernel_command(self):
        # kernel command
        response = self.client.post('{}/kernel'.format(self.BASE_URL))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_update_check_command(self):

        # update-check command
        response = self.client.post('{}/update-check'.format(self.BASE_URL))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_update_command(self):

        # update command
        response = self.client.post('{}/update'.format(self.BASE_URL))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_current_version_command(self):

        # current-version command
        response = self.client.post('{}/current-version'.format(self.BASE_URL))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_current_user_command(self):

        # current-user command
        response = self.client.post('{}/current-user'.format(self.BASE_URL))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_auto_update_status_command(self):
        # auto-update-status command
        response = self.client.post(
            '{}/auto-update-status'.format(self.BASE_URL))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_enable_auto_update_command(self):

        # enable-auto-update command
        response = self.client.post(
            '{}/enable-auto-update'.format(self.BASE_URL))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_disable_auto_update_command(self):

        # disable-auto-update command
        response = self.client.post(
            '{}/disable-auto-update'.format(self.BASE_URL))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_refresh_disk_state(self):

        # refresh-disk-state command
        response = self.client.post(
            '{}/refresh-disk-state'.format(self.BASE_URL))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_refresh_pool_state(self):

        # refresh-pool-state command
        response = self.client.post(
            '{}/refresh-pool-state'.format(self.BASE_URL))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_refresh_share_state(self):
        # refresh-share-state command
        response = self.client.post(
            '{}/refresh-share-state'.format(self.BASE_URL))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_refresh_snapshot_state(self):
        # refresh-snapshot-state command
        response = self.client.post(
            '{}/refresh-snapshot-state'.format(self.BASE_URL))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_shutdown(self):
        # shutdown command
        response = self.client.post('{}/shutdown'.format(self.BASE_URL))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_reboot(self):
        # reboot command
        response = self.client.post('{}/reboot'.format(self.BASE_URL))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
