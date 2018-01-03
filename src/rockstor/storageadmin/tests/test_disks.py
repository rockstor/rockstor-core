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


class DiskTests(APITestMixin, APITestCase):
    fixtures = ['fix1.json']
    BASE_URL = '/api/disks'

    @classmethod
    def setUpClass(cls):
        super(DiskTests, cls).setUpClass()

        # post mocks
        cls.patch_wipe_disk = patch('storageadmin.views.disk.wipe_disk')
        cls.mock_wipe_disk = cls.patch_wipe_disk.start()
        cls.mock_wipe_disk.return_value = 'out', 'err', 0

        cls.patch_scan_disks = patch('storageadmin.views.disk.scan_disks')
        cls.mock_scan_disks = cls.patch_scan_disks.start()

        cls.patch_blink_disk = patch('storageadmin.views.disk.blink_disk')
        cls.mock_blink_disk = cls.patch_blink_disk.start()

        cls.patch_pool_usage = patch('storageadmin.views.disk.pool_usage')
        cls.mock_pool_usage = cls.patch_pool_usage.start()
        cls.mock_pool_usage.return_value = (14680064, 10, 4194305)

        cls.patch_mount_root = patch('storageadmin.views.disk.mount_root')
        cls.mock_mount_root = cls.patch_mount_root.start()

        cls.patch_pool_raid = patch('storageadmin.views.disk.pool_raid')
        cls.mock_pool_raid = cls.patch_pool_raid.start()

        cls.patch_enable_quota = patch('storageadmin.views.disk.enable_quota')
        cls.mock_enable_quota = cls.patch_enable_quota.start()

    @classmethod
    def tearDownClass(cls):
        super(DiskTests, cls).tearDownClass()

    def test_disk_scan(self):
        response = self.client.post(('%s/scan' % self.BASE_URL), data=None,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_disk_wipe(self):
        url = ('%s/invalid/wipe' % self.BASE_URL)
        response = self.client.post(url, data=None, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR)
        e_msg = 'Disk id (invalid) does not exist.'
        self.assertEqual(response.data['detail'], e_msg)

    def test_invalid_command(self):
        url = ('%s/sdb/invalid' % self.BASE_URL)
        response = self.client.post(url, data=None, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR)
        e_msg = ('Unsupported command (invalid). Valid commands are; wipe, '
                 'btrfs-wipe, luks-format, btrfs-disk-import, blink-drive, '
                 'enable-smart, disable-smart, smartcustom-drive, '
                 'spindown-drive, pause, role-drive, '
                 'luks-drive.')
        self.assertEqual(response.data['detail'], e_msg)

    def test_disk_wipe(self):
        url = ('%s/sdb/wipe' % self.BASE_URL)
        response = self.client.post(url, data=None, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.mock_wipe_disk.side_effect = Exception()
        response = self.client.post(url, data=None, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR)
        # TODO: test need update - for
        e_msg = 'Failed to wipe the disk due to a system error.'
        self.assertEqual(response.data['detail'], e_msg)
        self.mock_wipe_disk.side_effect = None

    def test_btrfs_disk_import(self):
        url = ('%s/sdc/btrfs-disk-import' % self.BASE_URL)
        response = self.client.post(url, data=None, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_btrfs_wipe(self):
        url = ('%s/sdc/btrfs-wipe' % self.BASE_URL)
        response = self.client.post(url, data=None, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_blink_drive(self):
        url = ('%s/sdc/blink-drive' % self.BASE_URL)
        response = self.client.post(url, data=None, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_enable_smart(self):
        url = ('%s/sdd/enable-smart' % self.BASE_URL)
        response = self.client.post(url, data=None, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR)
        e_msg = 'S.M.A.R.T support is not available on Disk (sdd).'
        self.assertEqual(response.data['detail'], e_msg)

    def test_disable_smart(self):
        url = ('%s/sdd/disable-smart' % self.BASE_URL)
        response = self.client.post(url, data=None, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR)
        e_msg = 'S.M.A.R.T support is not available on Disk (sdd).'
        self.assertEqual(response.data['detail'], e_msg)
