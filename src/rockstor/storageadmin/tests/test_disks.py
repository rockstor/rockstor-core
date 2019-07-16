"""
Copyright (c) 2012-2019 RockStor, Inc. <http://rockstor.com>
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
import mock
from rest_framework import status
from rest_framework.test import APITestCase
from mock import patch

from storageadmin.models import Disk
from storageadmin.tests.test_api import APITestMixin


class DiskTests(APITestMixin, APITestCase):
    # fixtures = ['fix1.json']
    fixtures = ["test_disks.json"]
    BASE_URL = "/api/disks"

    @classmethod
    def setUpClass(cls):
        super(DiskTests, cls).setUpClass()

        # post mocks
        cls.patch_wipe_disk = patch("storageadmin.views.disk.wipe_disk")
        cls.mock_wipe_disk = cls.patch_wipe_disk.start()
        cls.mock_wipe_disk.return_value = "out", "err", 0

        cls.patch_scan_disks = patch("storageadmin.views.disk.scan_disks")
        cls.mock_scan_disks = cls.patch_scan_disks.start()

        cls.patch_blink_disk = patch("storageadmin.views.disk.blink_disk")
        cls.mock_blink_disk = cls.patch_blink_disk.start()

        cls.patch_mount_root = patch("storageadmin.views.disk.mount_root")
        cls.mock_mount_root = cls.patch_mount_root.start()

        cls.patch_pool_raid = patch("storageadmin.views.disk.pool_raid")
        cls.mock_pool_raid = cls.patch_pool_raid.start()
        cls.mock_pool_raid.return_value = {"data": "single", "metadata": "single"}

        cls.patch_enable_quota = patch("storageadmin.views.disk.enable_quota")
        cls.mock_enable_quota = cls.patch_enable_quota.start()

        cls.patch_import_shares = patch("storageadmin.views.disk.import_shares")
        cls.mock_import_shares = cls.patch_import_shares.start()

        # TODO: maybe patch as storageadmin.views.disk.smart.toggle_smart
        cls.patch_toggle_smart = patch("system.smart.toggle_smart")
        cls.mock_toggle_smart = cls.patch_toggle_smart.start()
        cls.mock_toggle_smart.return_value = [""], [""], 0

        # primarily for test_btrfs_disk_import (to emulate a successful import)
        cls.patch_get_pool_info = patch("storageadmin.views.disk.get_pool_info")
        cls.mock_get_pool_info = cls.patch_get_pool_info.start()
        cls.fake_pool_info = {
            "disks": ["mock-disk"],
            "label": "mock-label",
            "uuid": "b3d201a8-b497-4365-a90d-a50c50b8e808",
        }
        cls.mock_get_pool_info.return_value = cls.fake_pool_info

        cls.temp_disk = Disk(id=2, name="mock-disk", size=88025459, parted=False)

    @classmethod
    def tearDownClass(cls):
        super(DiskTests, cls).tearDownClass()

    def test_disk_scan(self):
        response = self.client.post(
            ("{}/scan".format(self.BASE_URL)), data=None, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_disk_wipe(self):
        fake_dId = 99999
        url = "{}/{}/wipe".format(self.BASE_URL, fake_dId)
        response = self.client.post(url, data=None, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        e_msg = "Disk id ({}) does not exist.".format(fake_dId)
        self.assertEqual(response.data[0], e_msg)

    def test_invalid_command(self):
        url = "{}/1/invalid".format(self.BASE_URL)
        response = self.client.post(url, data=None, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        e_msg = (
            "Unsupported command (invalid). Valid commands are; wipe, "
            "btrfs-wipe, luks-format, btrfs-disk-import, blink-drive, "
            "enable-smart, disable-smart, smartcustom-drive, "
            "spindown-drive, pause, role-drive, "
            "luks-drive."
        )
        self.assertEqual(response.data[0], e_msg)

    @mock.patch("storageadmin.views.disk.Disk")
    def test_disk_wipe(self, mock_disk):

        mock_disk.objects.get.return_value = self.temp_disk

        # btrfs-wipe is an aliase for wipe; ensure it exists.
        url = "{}/2/btrfs-wipe".format(self.BASE_URL)
        response = self.client.post(url, data=None, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = "{}/2/wipe".format(self.BASE_URL)
        response = self.client.post(url, data=None, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        e_msg = "mock example exception surfaced from wipe_disk()"
        self.mock_wipe_disk.side_effect = Exception(e_msg)
        response = self.client.post(url, data=None, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data[0], e_msg)
        self.mock_wipe_disk.side_effect = None

    @mock.patch("storageadmin.views.disk.Disk")
    def test_btrfs_disk_import(self, mock_disk):

        mock_disk.objects.get.return_value = self.temp_disk

        url = "{}/2/btrfs-disk-import".format(self.BASE_URL)
        response = self.client.post(url, data=None, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @mock.patch("storageadmin.views.disk.Disk")
    def test_btrfs_disk_import_fail(self, mock_disk):

        mock_disk.objects.get.return_value = self.temp_disk

        mock_e_msg = (
            "Error running a command. cmd = /sbin/btrfs fi show "
            "/dev/disk/by-id/{}. rc = 1. stdout = ['']. stderr = "
            "['ERROR: not a valid btrfs filesystem: /dev/disk/by-id/"
            "{}', '']"
        ).format(self.temp_disk.name, self.temp_disk.name)

        self.mock_get_pool_info.side_effect = Exception(mock_e_msg)

        url = "{}/2/btrfs-disk-import".format(self.BASE_URL)
        response = self.client.post(url, data=None, format="json")
        e_msg = (
            "Failed to import any pool on device db id ({}). "
            "Error: ({}).".format(self.temp_disk.id, mock_e_msg)
        )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

        self.assertEqual(response.data[0], e_msg)

    @mock.patch("storageadmin.views.disk.Disk")
    def test_blink_drive(self, mock_disk):

        mock_disk.objects.get.return_value = self.temp_disk

        url = "{}/2/blink-drive".format(self.BASE_URL)
        response = self.client.post(url, data=None, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @mock.patch("storageadmin.views.disk.Disk")
    def test_enable_smart(self, mock_disk):

        mock_disk.objects.get.return_value = self.temp_disk

        url = "{}/2/enable-smart".format(self.BASE_URL)
        response = self.client.post(url, data=None, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        e_msg = "S.M.A.R.T support is not available on disk ({}).".format(
            self.temp_disk.name
        )
        self.assertEqual(response.data[0], e_msg)

    @mock.patch("storageadmin.views.disk.Disk")
    def test_enable_smart_when_available(self, mock_disk):

        self.temp_disk.smart_available = True
        mock_disk.objects.get.return_value = self.temp_disk

        url = "{}/2/enable-smart".format(self.BASE_URL)
        response = self.client.post(url, data=None, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @mock.patch("storageadmin.views.disk.Disk")
    def test_disable_smart(self, mock_disk):

        mock_disk.objects.get.return_value = self.temp_disk

        url = "{}/2/disable-smart".format(self.BASE_URL)
        response = self.client.post(url, data=None, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        e_msg = "S.M.A.R.T support is not available on disk ({}).".format(
            self.temp_disk.name
        )
        self.assertEqual(response.data[0], e_msg)
