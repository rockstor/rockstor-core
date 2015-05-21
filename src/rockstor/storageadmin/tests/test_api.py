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

# from rest_framework import status
# from rest_framework.test import APITestCase
# import mock
# from mock import patch
#
# # TODO inheritance structure... functionality for all API tests.
#
# class RockstorAPITests(APITestCase):
#     # fixtures = ['fix1.json']
#     # BASE_URL = '/api/shares'
#
#     @classmethod
#     def setUpClass(self):
#
#         # post mocks
#         self.patch_mount_root = patch('storageadmin.views.pool.mount_root')
#         self.mock_mount_root = self.patch_mount_root.start()
#         self.mock_mount_root.return_value = 'foo'
#
#         self.patch_add_pool = patch('storageadmin.views.pool.add_pool')
#         self.mock_add_pool = self.patch_add_pool.start()
#         self.mock_add_pool.return_value = True
#
#         self.patch_pool_usage = patch('storageadmin.views.pool.pool_usage')
#         self.mock_pool_usage = self.patch_pool_usage.start()
#         self.mock_pool_usage.return_value = (100, 10, 90)
#
#         self.patch_btrfs_uuid = patch('storageadmin.views.pool.btrfs_uuid')
#         self.mock_btrfs_uuid = self.patch_btrfs_uuid.start()
#         self.mock_btrfs_uuid.return_value = 'bar'
#
#         # put mocks (also uses pool_usage)
#         self.patch_resize_pool = patch('storageadmin.views.pool.resize_pool')
#         self.mock_resize_pool = self.patch_resize_pool.start()
#         self.mock_resize_pool = True
#
#         self.patch_balance_start = patch('storageadmin.views.pool.balance_start')
#         self.mock_balance_start = self.patch_balance_start.start()
#         self.mock_balance_start.return_value = 1
#
#         # delete mocks
#         self.patch_umount_root = patch('storageadmin.views.pool.umount_root')
#         self.mock_umount_root = self.patch_umount_root.start()
#         self.mock_umount_root.return_value = True
#
#         # remount mocks
#         self.patch_remount = patch('storageadmin.views.pool.remount')
#         self.mock_remount = self.patch_remount.start()
#         self.mock_remount.return_value = True
#
#         # error handling run_command mocks
#         self.patch_run_command = patch('storageadmin.util.run_command')
#         self.mock_run_command = self.patch_run_command.start()
#         self.mock_run_command.return_value = True
#
#     @classmethod
#     def tearDownClass(self):
#         patch.stopall()
#
#     def setUp(self):
#         self.client.login(username='admin', password='admin')
#
#     def test_auth(self):
#         """
#         unauthorized api access
#         """
#         self.client.logout()
#         response = self.client.get(self.BASE_URL)
#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
#
#     def test_get(self):
#         """
#         get on the base url.
#         """
#         response1 = self.client.get(self.BASE_URL)
#         self.assertEqual(response1.status_code, status.HTTP_200_OK, msg=response1.data)