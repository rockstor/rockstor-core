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

from storageadmin.models import Snapshot, Share, Pool
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
        # cls.mock_qgroup_assign.return_value = 1
        cls.mock_qgroup_assign.return_value = True

        # Changed from share_usage to volume_usage, potential issue as
        # Potential issue here as volume_usage returns either 2 or 4 values
        # When called with 2 parameters (pool, volume_id) it returns 2 values.
        # But with 3 parameters (pool, volume_id, pvolume_id) it returns 4
        # values if the last parameter is != None.
        cls.patch_volume_usage = patch('storageadmin.views.snapshot.'
                                       'volume_usage')
        cls.mock_volume_usage = cls.patch_volume_usage.start()
        cls.mock_volume_usage.return_value = 16, 16

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

    def test_post_requests_1(self):
        """
        invalid snapshot post operation via invalid share name
        """
        # Invalid share name
        data = {'snapshot-name': 'snap3', 'shares': 'invalid', 'writable':
                'rw', 'uvisible': 'invalid'}
        snap_name = 'snap3'
        share_name = 'invalid'
        share_id = 99999  # invalid share id for invalid share name.
        response = self.client.post(
            '{}/{}/snapshots/{}'.format(self.BASE_URL, share_id, snap_name),
            data=data, sname=share_name, snap_name=snap_name)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = "Share with id ({}) does not exist.".format(share_id)
        self.assertEqual(response.data[0], e_msg)

    @mock.patch('storageadmin.views.snapshot.Share')
    @mock.patch('storageadmin.views.share.Pool')
    @mock.patch('storageadmin.views.snapshot.NFSExport')
    def test_post_requests_2(self, mock_nfs, mock_pool, mock_share):
        """
        1. Create snapshot providing invalid uvisible bool type
        2. Create snapshot providing invalid writable bool type
        3. happy path to create snapshot
        2. Create a snapshot with duplicate name
        """

        temp_pool = Pool(id=1, name='rockstor_rockstor', size=88025459)
        mock_pool.objects.get.return_value = temp_pool

        temp_share = Share(id=3, name='share1', pool=temp_pool, size=8025459)
        mock_share.objects.get.return_value = temp_share
        # mock_snapshot.objects.get.side_effect = Snapshot.DoesNotExist

        # Invalid uvisible bool type
        data = {'snapshot-name': 'snap3', 'shares': 'share1',
                'writable': False, 'uvisible': 'invalid'}
        snap_name = 'snap3'
        share_name = 'share1'
        share_id = 3  # from fix5.json
        response = self.client.post(
            '%s/%s/snapshots/%s' % (self.BASE_URL, share_id, snap_name),
            data=data, sname=share_name, snap_name=snap_name)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = "Element 'uvisible' must be a boolean, not (<type 'unicode'>)."
        self.assertEqual(response.data[0], e_msg)

        # Invalid writable bool type
        data = {'snapshot-name': 'snap3', 'shares': 'share1',
                'writable': 'invalid', 'uvisible': True}
        snap_name = 'snap3'
        share = 'share1'
        share_id = 3  # from fix5.json and above mocking object
        mock_nfs.objects.filter(share=share).exists.return_value = True
        response = self.client.post(
            '{}/{}/snapshots/{}'.format(self.BASE_URL, share_id, snap_name),
            data=data, sname=share, snap_name=snap_name)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        # TODO consider changing tested code to unify quota types to single
        # as per "Invalid uvisible bool type" to remove need for escaping here.
        e_msg = ('Element "writable" must be a boolean, not '
                 '(<type \'unicode\'>).')
        self.assertEqual(response.data[0], e_msg)

        # # Happy Path creating a snapshot by name snap3
        data = {'snapshot-name': 'snap3', 'shares': 'share1',
                'writable': False, 'uvisible': False}
        snap_name = 'snap3'
        share = 'share1'
        share_id = 3  # from fix5.json and above mocking object
        mock_nfs.objects.filter(share=share).exists.return_value = True
        response = self.client.post(
            '{}/{}/snapshots/{}'.format(self.BASE_URL, share_id, snap_name),
            data=data, sname=share, snap_name=snap_name)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # # Create duplicate snapshot by name snap3
        data = {'snapshot-name': 'snap2', 'shares': 'share2',
                'writable': True, 'uvisible': True}
        snap_name = 'snap3'
        share_name = 'share1'
        share_id = 3  # from fix5.json
        response = self.client.post(
            '{}/{}/snapshots/{}'.format(self.BASE_URL, share_id, snap_name),
            data=data, sname=share_name, snap_name=snap_name)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Snapshot ({}) already exists for the '
                 'share ({}).').format(snap_name, share_name)
        self.assertEqual(response.data[0], e_msg)

    @mock.patch('storageadmin.views.share_command.Snapshot')
    @mock.patch('storageadmin.views.snapshot.Share')
    @mock.patch('storageadmin.views.share.Pool')
    def test_clone_command(self, mock_pool, mock_share, mock_snapshot):

        temp_pool = Pool(id=1, name='rockstor_rockstor', size=88025459)
        mock_pool.objects.get.return_value = temp_pool

        temp_share = Share(id=4, name='share2', pool=temp_pool, size=8025459)
        mock_share.objects.get.return_value = temp_share
        mock_snapshot.objects.get.side_effect = Snapshot.DoesNotExist

        data = {'name': 'clonesnap2'}
        snap_name = 'clonesnap2'
        share = 'share2'
        share_id = 4  # from fix5.json
        response = self.client.post(
            '{}/{}/snapshots/{}'.format(self.BASE_URL, share_id, snap_name),
            data=data, sname=share, snap_name=snap_name, command='clone')
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    @mock.patch('storageadmin.views.share_command.Snapshot')
    @mock.patch('storageadmin.views.snapshot.Share')
    @mock.patch('storageadmin.views.share.Pool')
    def test_delete_requests(self, mock_pool, mock_share, mock_snapshot):
        """
        1. Delete snapshot that does not exist
        2. Delete snapshot with no name specified
        """

        temp_pool = Pool(id=1, name='rockstor_rockstor', size=88025459)
        mock_pool.objects.get.return_value = temp_pool

        temp_share = Share(id=3, name='share1', pool=temp_pool, size=8025459)
        mock_share.objects.get.return_value = temp_share

        mock_snapshot.objects.get.side_effect = Snapshot.DoesNotExist

        # # Delete snapshot that does not exists
        snap_name = 'snap3'
        share_name = 'share1'
        share_id = 3  # from fix5.json
        response = self.client.delete(
            '{}/{}/snapshots/{}'.format(self.BASE_URL, share_id, snap_name))
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = 'Snapshot name (snap3) does not exist.'
        self.assertEqual(response.data[0], e_msg)

        temp_share2 = Share(id=4, name='share2', pool=temp_pool, size=8025459)
        mock_share.objects.get.return_value = temp_share2

        # Delete without snapshot name
        share_name = 'share1'
        share_id = 3  # from fix5.json
        response = self.client.delete('{}/{}/snapshots'.format(self.BASE_URL,
                                                               share_id))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # # Delete snapshot happy path
        # # creating a snapshot just for the next test.
        # # TODO: replace this repeat post test with a proper mock of a snapshot
        # # ie attempted to use:
        #
        # # temp_snap = Snapshot(id=2, name='snap2', share=temp_share2,
        # #                      snap_type='admin')
        # # mock_snapshot.objects.get.return_value = temp_snap
        # # mock_snapshot.objects.filter(share='share2', name='snap2'
        # #                              ).exists.return_value = True
        # # but received:
        # # 'Snapshot name (snap2) does not exist.'
        #
        # data = {'snapshot-name': 'snap2', 'shares': 'share2',
        #         'writable': False, 'uvisible': False}
        # snap_name = 'snap2'
        # share = 'share2'
        # share_id = 4
        # response = self.client.post(
        #     '{}/{}/snapshots/{}'.format(self.BASE_URL, share_id, snap_name),
        #     data=data, sname=share, snap_name=snap_name)
        # self.assertEqual(response.status_code,
        #                  status.HTTP_200_OK, msg=response.data)
        # # now move to our happy path delete test of just created 'snap2'
        # response = self.client.delete(
        #     '{}/{}/snapshots/{}'.format(self.BASE_URL, share_id, snap_name))
        # self.assertEqual(response.status_code,
        #                  status.HTTP_200_OK, msg=response.data)
