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
import mock
from mock import patch
from storageadmin.tests.test_api import APITestMixin

"""Using fixture fix5.json where hard coded data to pre-populate database
before the tests run.  Created pool1 Created share1, share2 using pool1 Created
snapshot snap1 for share1 with uvisible false Created snapshot snap2 for share2
with uvisible True

"""


class SnapshotTests(APITestMixin, APITestCase):
    fixtures = ['fix5.json']
    BASE_URL = '/api/shares'

    @classmethod
    def setUpClass(cls):
        super(SnapshotTests, cls).setUpClass()

        # post mocks

        cls.patch_add_snap = patch('storageadmin.views.snapshot.add_snap')
        cls.mock_add_snap = cls.patch_add_snap.start()
        cls.mock_add_snap.return_value = 'out', 'err', 0

        cls.patch_share_id = patch('storageadmin.views.snapshot.share_id')
        cls.mock_share_id = cls.patch_share_id.start()
        cls.mock_share_id.return_value = 1

        cls.patch_qgroup_assign = patch('storageadmin.views.snapshot.'
                                        'qgroup_assign')
        cls.mock_qgroup_assign = cls.patch_qgroup_assign.start()
        cls.mock_qgroup_assign.return_value = 1

        cls.patch_share_usage = patch('storageadmin.views.snapshot.'
                                      'share_usage')
        cls.mock_share_usage = cls.patch_share_usage.start()
        cls.mock_share_usage.return_value = 16, 16

        cls.patch_share_usage = patch('storageadmin.views.snapshot.'
                                      'share_usage')
        cls.mock_share_usage = cls.patch_share_usage.start()
        cls.mock_share_usage.return_value = 16, 16

        cls.patch_mount_snap = patch('storageadmin.views.snapshot.mount_snap')
        cls.mock_mount_snap = cls.patch_mount_snap.start()
        cls.mock_mount_snap.return_value = 'out', 'err', 0

        cls.patch_remove_snap = patch('storageadmin.views.snapshot.'
                                      'remove_snap')
        cls.mock_remove_snap = cls.patch_remove_snap.start()
        cls.mock_remove_snap.return_value = True

        cls.patch_create_clone = patch('storageadmin.views.snapshot.'
                                       'create_clone')
        cls.mock_create_clone = cls.patch_create_clone.start()

    @classmethod
    def tearDownClass(cls):
        super(SnapshotTests, cls).tearDownClass()

    def test_get(self):
        """
        Test GET request
        1. Get base URL
        """

        response = self.client.get('/api/snapshots')
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)

    @mock.patch('storageadmin.views.snapshot.NFSExport')
    def test_post_requests(self, mock_nfs):
        """
        invalid snapshot post operations
        1. Create snapshot providing invalid share name
        2. Create a snapshot with duplicate name
        """
        # Invalid share name
        data = {'snapshot-name': 'snap3', 'shares': 'invalid', 'writable':
                'rw', 'uvisible': 'invalid'}
        snap_name = 'snap3'
        share_name = 'invalid'
        response = self.client.post(
            '%s/%s/snapshots/%s' % (self.BASE_URL, share_name, snap_name),
            data=data, sname=share_name, snap_name=snap_name)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ("Share: invalid does not exist")
        self.assertEqual(response.data['detail'], e_msg)

        # Invalid uvisible bool type
        data = {'snapshot-name': 'snap3', 'shares': 'share1', 'writable': 'rw',
                'uvisible': 'invalid'}
        snap_name = 'snap3'
        share_name = 'share1'
        response = self.client.post(
            '%s/%s/snapshots/%s' % (self.BASE_URL, share_name, snap_name),
            data=data, sname=share_name, snap_name=snap_name)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ("uvisible must be a boolean, not <type 'unicode'>")
        self.assertEqual(response.data['detail'], e_msg)

        # Create duplicate snapshot
        data = {'snapshot-name': 'snap2', 'shares': 'share2', 'writable': 'rw',
                'uvisible': True}
        snap_name = 'snap2'
        share_name = 'share2'
        response = self.client.post(
            '%s/%s/snapshots/%s' % (self.BASE_URL, share_name, snap_name),
            data=data, sname=share_name, snap_name=snap_name)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ("Snapshot(snap2) already exists for the Share(share2).")
        self.assertEqual(response.data['detail'], e_msg)

        # Happy Path
        data = {'snapshot-name': 'snap3', 'shares': 'share1', 'writable': 'rw',
                'uvisible': True}
        snap_name = 'snap3'
        share = 'share1'
        mock_nfs.objects.filter(share=share).exists.return_value = True
        response = self.client.post(
            '%s/%s/snapshots/%s' % (self.BASE_URL, share, snap_name),
            data=data, sname=share, snap_name=snap_name)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_clone_command(self):
        data = {'name': 'clonesnap2'}
        snap_name = 'clonesnap2'
        share = 'share2'
        response = self.client.post(
            '%s/%s/snapshots/%s' % (self.BASE_URL, share, snap_name),
            data=data, sname=share, snap_name=snap_name, command='clone')
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_delete_requests(self):
        """
        1. Delete snapshot that does not exist
        2. Delete snapshot
        """
        # Delete snapshot that does not exists
        snap_name = 'snap3'
        share_name = 'share1'

        response = self.client.delete('%s/%s/snapshots/%s' %
                                      (self.BASE_URL, share_name, snap_name))
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Snapshot(snap3) does not exist.')
        self.assertEqual(response.data['detail'], e_msg)

        # Delete without snapshot name

        share_name = 'share1'
        response = self.client.delete('%s/%s/snapshots' %
                                      (self.BASE_URL, share_name))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # Delete happy path
        snap_name = 'snap2'
        share_name = 'share2'
        response = self.client.delete('%s/%s/snapshots/%s' %
                                      (self.BASE_URL, share_name, snap_name))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
