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
from storageadmin.models import Pool, Share


class ShareTests(APITestMixin, APITestCase):
    fixtures = ['test_shares.json']
    BASE_URL = '/api/shares'

    @classmethod
    def setUpClass(cls):
        super(ShareTests, cls).setUpClass()

        # post mocks
        cls.patch_add_share = patch('storageadmin.views.share.add_share')
        cls.mock_add_share = cls.patch_add_share.start()
        cls.mock_add_share.return_value = True

        cls.patch_update_quota = patch('storageadmin.views.share.update_quota')
        cls.mock_update_quota = cls.patch_update_quota.start()
        cls.mock_update_quota.return_value = True

        # "is_share_mounted" is now a Share model property of Share.is_mounted.
        # cls.patch_is_share_mounted = patch('storageadmin.views.share.'
        #                                    'is_share_mounted')
        # cls.mock_is_share_mounted = cls.patch_is_share_mounted.start()
        # cls.mock_is_share_mounted.return_value = False

        cls.patch_set_property = patch('storageadmin.views.share.set_property')
        cls.mock_set_property = cls.patch_set_property.start()
        cls.mock_set_property.return_value = True

        cls.patch_mount_share = patch('storageadmin.views.share.mount_share')
        cls.mock_mount_share = cls.patch_mount_share.start()
        cls.mock_mount_share.return_value = True

        cls.patch_qgroup_id = patch('storageadmin.views.share.qgroup_id')
        cls.mock_qgroup_id = cls.patch_qgroup_id.start()
        cls.mock_qgroup_id.return_value = '0f123f'

        cls.patch_qgroup_create = patch('storageadmin.views.share.'
                                        'qgroup_create')
        cls.mock_qgroup_create = cls.patch_qgroup_create.start()
        cls.mock_qgroup_create.return_value = '1'

        # put mocks
        # change share_usage to volume_usage
        # cls.patch_share_usage = patch('storageadmin.views.share.share_usage')
        # cls.mock_share_usage = cls.patch_share_usage.start()
        # cls.mock_share_usage.return_value = (500, 500)

        cls.patch_volume_usage = patch('storageadmin.views.share.volume_usage')
        cls.mock_volume_usage = cls.patch_volume_usage.start()
        # potential issue here as volume_usage returns either 2 or 4 values
        # When called with 2 parameters (pool, volume_id) it returns 2 values.
        # But with 3 parameters (pool, volume_id, pvolume_id) it returns 4
        # values if the last parameter is != None.
        cls.mock_volume_usage.return_value = (500, 500)

        # delete mocks
        cls.patch_remove_share = patch('storageadmin.views.share.remove_share')
        cls.mock_remove_share = cls.patch_remove_share.start()
        cls.mock_remove_share.return_value = True

    @classmethod
    def tearDownClass(cls):
        super(ShareTests, cls).tearDownClass()

    def test_get(self):
        """
        Test GET request
        1. Get base URL
        2. Get existing share
        3. Get nonexistant share
        4. Get w/ sort parameters
        """
        self.get_base(self.BASE_URL)

        # get share share1 (already existing share in fixture fix1 with id5)
        sId = 5
        response = self.client.get('{}/{}'.format(self.BASE_URL, sId))
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response)

        # get share that does not exist
        sId = 99999
        response = self.client.get('{}/{}'.format(self.BASE_URL, sId))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND,
                         msg=response)

        # Get w/ sort parameters
        response1 = self.client.get('%s?sortby=usage&reverse=yes' %
                                    self.BASE_URL)
        self.assertEqual(response1.status_code, status.HTTP_200_OK,
                         msg=response1.data)

        response2 = self.client.get('%s?sortby=usage' % self.BASE_URL)
        self.assertEqual(response1.status_code, status.HTTP_200_OK,
                         msg=response2.data)

    @mock.patch('storageadmin.views.share.Pool')
    def test_name_regex(self, mock_pool):
        """Share name must start with a alphanumeric(a-z0-9) ' 'character and
        can be followed by any of the ' 'following characters: letter(a-z),
        digits(0-9), ' 'hyphen(-), underscore(_) or a period(.).'  1. Test a
        few valid regexes (eg: share1, Myshare, 123, etc..)  2. Test a few
        invalid regexes (eg: -share1, .share etc..)  3. Empty string for share
        name 4. max length(254 characters) for share name 5. max length + 1 for
        share name

        """

        class MockPool(object):
            def __init__(self, **kwargs):
                self.id = 1
                self.name = 'rockstor_rockstor'
                self.size = 7025459

        mock_pool.objects.get.side_effect = MockPool

        # valid share names
        # pool id for rockstor_rockstor = 1
        data = {'pool': 'rockstor_rockstor', 'size': 1000}
        valid_names = ('123share', 'SHARE_TEST', 'Zzzz...', '1234', 'myshare',
                       'Sha' + 'r' * 250 + 'e',)

        for sname in valid_names:
            data['sname'] = sname
            response = self.client.post(self.BASE_URL, data=data)
            self.assertEqual(response.status_code, status.HTTP_200_OK,
                             msg=response.data)
            self.assertEqual(response.data['name'], sname)

        # invalid pool names
        # e_msg = ('Share name must start with a alphanumeric(a-z0-9) character '
        #          'and can be followed by any of the following characters: '
        #          'letter(a-z), digits(0-9), hyphen(-), underscore(_) or a '
        #          'period(.).')
        # TODO Test needs updating
        e_msg = ('Invalid characters in share name. Following are '
                 'allowed: letter(a-z or A-Z), digit(0-9), '
                 'hyphen(-), underscore(_) or a period(.).')

        invalid_names = ('Share $', '-share', '.share', '', ' ',)
        for sname in invalid_names:
            data['sname'] = sname
            response = self.client.post(self.BASE_URL, data=data)
            self.assertEqual(response.status_code,
                             status.HTTP_500_INTERNAL_SERVER_ERROR,
                             msg=response.data)
            self.assertEqual(response.data[0], e_msg)

        # Share name with more than 255 characters
        e_msg = 'Share name length cannot exceed 254 characters.'

        data['sname'] = 'Sh' + 'a' * 251 + 're'
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data[0], e_msg)

    def test_create(self):
        """
        Test POST request to create shares
        1. Create share on a nonexistent pool
        2. Create share on root pool
        3. Create share with invalid compression
        4. Create share with invalid sizes
        5. Create share with duplicate names
        6. Create share with valid replica
        7. Create share with invalid replica
        8. Create share with share size > pool size
        """
        # create a share on a pool that does not exist
        data = {'sname': 'rootshare', 'pool': 'does_not_exist',
                'size': 1048576}
        e_msg = 'Pool (does_not_exist) does not exist.'
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data[0], e_msg)

        # create a share on root pool
        data['pool'] = 'rockstor_rockstor'
        response2 = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response2.status_code, status.HTTP_200_OK,
                         msg=response2.data)
        self.assertEqual(response2.data['name'], 'rootshare')

        # create a share with invalid compression
        data['compression'] = 'invalid'
        e_msg2 = ("Unsupported compression algorithm (invalid). Use one of "
                  "('lzo', 'zlib', 'no')")
        response3 = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response3.data)
        self.assertEqual(response3.data[0], e_msg2)

        # create a share with invalid size (too small)
        data2 = {'sname': 'too_small', 'pool': 'rockstor_rockstor', 'size': 1}
        e_msg3 = 'Share size should be at least 100 KB. Given size is 1 KB.'
        response4 = self.client.post(self.BASE_URL, data=data2)
        self.assertEqual(response4.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response4.data)
        self.assertEqual(response4.data[0], e_msg3)

        # create a share with invalid size (non integer)
        data2['size'] = 'non int'
        e_msg4 = 'Share size must be an integer.'
        response5 = self.client.post(self.BASE_URL, data=data2)
        self.assertEqual(response5.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response5.data)
        self.assertEqual(response5.data[0], e_msg4)

        # create share with same name as a pool that already exists
        data3 = {'sname': 'rockstor_rockstor', 'pool': 'rockstor_rockstor',
                 'size': 1048576}
        e_msg5 = ('A pool with this name (rockstor_rockstor) exists. Share '
                  'and pool names must be distinct. Choose '
                  'a different name.')
        response6 = self.client.post(self.BASE_URL, data=data3)
        self.assertEqual(response6.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response6.data)
        self.assertEqual(response6.data[0], e_msg5)

        # create share with name that already exists
        data3['sname'] = 'rootshare'
        e_msg6 = 'Share (rootshare) already exists. Choose a different name.'
        response7 = self.client.post(self.BASE_URL, data=data3)
        self.assertEqual(response7.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response7.data)
        self.assertEqual(response7.data[0], e_msg6)

        # create share with valid replica
        data4 = {'sname': 'valid_replica', 'pool': 'rockstor_rockstor',
                 'size': 100, 'replica': True}
        response8 = self.client.post(self.BASE_URL, data=data4)
        self.assertEqual(response8.status_code, status.HTTP_200_OK,
                         msg=response8.data)
        self.assertEqual(response8.data['name'], 'valid_replica')
        self.assertEqual(response8.data['replica'], True)

        # create share with invalid replica
        data5 = {'sname': 'invalid_replica', 'pool': 'rockstor_rockstor',
                 'size': 100, 'replica': 'non-bool'}
        e_msg7 = "Replica must be a boolean, not (<type 'unicode'>)."
        response9 = self.client.post(self.BASE_URL, data=data5)
        self.assertEqual(response9.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response9.data)
        self.assertEqual(response9.data[0], e_msg7)

        # create share with size > pool size
        data6 = {'sname': 'too_big', 'pool': 'rockstor_rockstor', 'size':
                 10000000000000}
        response8 = self.client.post(self.BASE_URL, data=data6)
        self.assertEqual(response8.status_code, status.HTTP_200_OK,
                         msg=response8.data)
        self.assertEqual(response8.data['name'], 'too_big')
        pool = Pool.objects.get(name=data6['pool'])
        self.assertEqual(response8.data['size'], pool.size)

    @mock.patch('storageadmin.views.share.Pool')
    def test_resize(self, mock_pool):
        """
        Test PUT request to update size of share
        1. Create valid share
        2. Valid resize
        3. Resize nonexistent share
        4. Resize share below current usage value
        5. Resize share below minimum 100KB
        """

        class MockPool(object):
            def __init__(self, **kwargs):
                self.id = 1
                self.name = 'rockstor_rockstor'
                self.size = 7025459

        mock_pool.objects.get.side_effect = MockPool

        # create new share
        data = {'sname': 'share2', 'pool': 'rockstor_rockstor', 'size': 1000}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response.data['name'], 'share2')
        self.assertEqual(response.data['size'], 1000)

        # resize share
        data3 = {'size': 2000, }
        response3 = self.client.put('%s/share1' % self.BASE_URL, data=data3)
        self.assertEqual(response3.status_code, status.HTTP_200_OK,
                         msg=response3.data)
        self.assertEqual(response3.data['size'], 2000)

        # resize a 'root' share
        data3 = {'size': 1500}
        response3 = self.client.put('%s/root' % self.BASE_URL, data=data3)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response3.data)
        e_msg = ('Operation not permitted on this share (root) because it is '
                 'a special system share.')
        self.assertEqual(response3.data[0], e_msg)

        # resize a 'home' share
        data3 = {'size': 1500}
        response3 = self.client.put('%s/home' % self.BASE_URL, data=data3)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response3.data)
        e_msg = ('Operation not permitted on this share (home) because it is '
                 'a special system share.')
        self.assertEqual(response3.data[0], e_msg)

        # resize to below current share usage value
        data3 = {'size': 400}
        response3 = self.client.put('%s/share1' % self.BASE_URL, data=data3)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response3.data)
        e_msg = ('Unable to resize because requested new size (400KB) is less '
                 'than current usage (500KB) of the share.')
        self.assertEqual(response3.data[0], e_msg)

        # resize below 100KB
        self.mock_share_usage.return_value = 50
        data3 = {'size': 99}
        response3 = self.client.put('%s/share1' % self.BASE_URL, data=data3)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response3.data)
        e_msg = 'Share size should be at least 100 KB. Given size is 99 KB.'
        self.assertEqual(response3.data[0], e_msg)

        # resize a share that doesn't exist
        data3 = {'sname': 'invalid', 'size': 1500}
        response3 = self.client.put('%s/invalid' % self.BASE_URL, data=data3)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response3.data)
        e_msg = 'Share id (invalid) does not exist.'
        self.assertEqual(response3.data[0], e_msg)

    def test_compression(self):
        """
        Test PUT request to update share compression_algo
        1. Create a share with invalid compression
        2. Create a share with zlib compression
        3. Create a share with lzo compression
        4. change compression from zlib to lzo
        5. change compression from lzo to zlib
        6. disable zlib, enable zlib
        7. disable lzo, enable lzo
        """

        # create share with invalid compression
        data = {'sname': 'rootshare', 'pool': 'rockstor_rockstor',
                'size': 100, 'compression': 'derp'}
        e_msg = ("Unsupported compression algorithm (derp). "
                 "Use one of ('lzo', 'zlib', 'no').")
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data[0], e_msg)

        # create share with zlib compression
        data['compression'] = 'zlib'
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        # self.assertEqual(response.data, 'derp')
        self.assertEqual(response.data['compression_algo'], 'zlib')

        # create share with lzo compression
        data2 = {'sname': 'share2', 'pool': 'rockstor_rockstor', 'size': 100,
                 'compression': 'lzo'}
        response2 = self.client.post(self.BASE_URL, data=data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK,
                         msg=response2.data)
        self.assertEqual(response2.data['compression_algo'], 'lzo')

        # change compression from zlib to lzo
        data3 = {'compression': 'lzo'}
        response3 = self.client.put('%s/rootshare' % self.BASE_URL, data=data3)
        self.assertEqual(response3.status_code, status.HTTP_200_OK,
                         msg=response3.data)
        self.assertEqual(response3.data['compression_algo'], 'lzo')

        # change compression from lzo to zlib
        data4 = {'compression': 'zlib'}
        response4 = self.client.put('%s/share2' % self.BASE_URL, data=data4)
        self.assertEqual(response4.status_code, status.HTTP_200_OK,
                         msg=response4.data)
        self.assertEqual(response4.data['compression_algo'], 'zlib')

        # disable zlib compression
        data5 = {'compression': 'no'}
        response5 = self.client.put('%s/share2' % self.BASE_URL, data=data5)
        self.assertEqual(response5.status_code, status.HTTP_200_OK,
                         msg=response5.data)
        self.assertEqual(response5.data['compression_algo'], 'no')

        # enable zlib compression
        response6 = self.client.put('%s/share2' % self.BASE_URL, data=data4)
        self.assertEqual(response6.status_code, status.HTTP_200_OK,
                         msg=response6.data)
        self.assertEqual(response6.data['compression_algo'], 'zlib')

        # disable lzo compression
        response7 = self.client.put('%s/rootshare' % self.BASE_URL, data=data5)
        self.assertEqual(response7.status_code, status.HTTP_200_OK,
                         msg=response7.data)
        self.assertEqual(response7.data['compression_algo'], 'no')

        # enable lzo compression
        response8 = self.client.put('%s/rootshare' % self.BASE_URL, data=data3)
        self.assertEqual(response8.status_code, status.HTTP_200_OK,
                         msg=response8.data)
        self.assertEqual(response8.data['compression_algo'], 'lzo')

    @mock.patch('storageadmin.views.share.remove_share')
    @mock.patch('storageadmin.views.share.SFTP')
    @mock.patch('storageadmin.views.share.SambaShare')
    @mock.patch('storageadmin.views.share.NFSExport')
    @mock.patch('storageadmin.views.share.Snapshot')
    def test_delete_set1(self, mock_snapshot, mock_nfs, mock_samba, mock_sftp,
                         mock_remove_share):
        """
        Test DELETE request on share
        1. Create valid share
        2. Delete share with replication related snapshots
        3. Delete share with NFS export
        4. Delete share that is shared via Samba
        5. Delete share with snapshots
        6. Delete share with SFTP export
        7. Delete share with remove_share failure (share still mounted)
        8. Delete nonexistent share
        """
        # create share
        data = {'sname': 'rootshare', 'pool': 'rockstor_rockstor', 'size': 100}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response.data['name'], 'rootshare')
        share = Share.objects.get(name='rootshare')

        # Delete share with replication related snapshots
        mock_snapshot.objects.filter(
            share=share, snap_type='replication').exists.return_value = True
        e_msg = ('Share (rootshare) cannot be deleted as it has replication '
                 'related snapshots.')
        response2 = self.client.delete('%s/rootshare' % self.BASE_URL)
        self.assertEqual(response2.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response2.data)
        self.assertEqual(response2.data[0], e_msg)
        mock_snapshot.objects.filter(
            share=share, snap_type='replication').exists.return_value = False

        # Delete share with NFS export
        mock_nfs.objects.filter(share=share).exists.return_value = True
        e_msg = ('Share (rootshare) cannot be deleted as it is exported via '
                 'NFS. Delete NFS exports and try again.')
        response3 = self.client.delete('%s/rootshare' % self.BASE_URL)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response3.data)
        self.assertEqual(response3.data[0], e_msg)
        mock_nfs.objects.filter(share=share).exists.return_value = False

        # Delete share that is shared via Samba
        mock_samba.objects.filter(share=share).exists.return_value = True
        e_msg = ('Share (rootshare) cannot be deleted as it is shared via '
                 'Samba. Unshare and try again.')
        response4 = self.client.delete('%s/rootshare' % self.BASE_URL)
        self.assertEqual(response4.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response4.data)
        self.assertEqual(response4.data[0], e_msg)
        mock_samba.objects.filter(share=share).exists.return_value = False

        # Delete share with SFTP export
        mock_sftp.objects.filter(share=share).exists.return_value = True
        e_msg = ('Share (rootshare) cannot be deleted as it is exported via '
                 'SFTP. Delete SFTP export and try again')
        response6 = self.client.delete('%s/rootshare' % self.BASE_URL)
        self.assertEqual(response6.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response6.data)
        self.assertEqual(response6.data[0], e_msg)
        mock_sftp.objects.filter(share=share).exists.return_value = False

        # Delete share with snapshots
        # TODO this test get triggered by check for snap_type='replication'
        mock_snapshot.objects.filter(
            share=share, snap_type='admin').exists.return_value = True
        e_msg = ('Share (rootshare) cannot be deleted as it has snapshots. '
                 'Delete snapshots and try again.')
        response5 = self.client.delete('%s/rootshare' % self.BASE_URL)
        self.assertEqual(response5.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response5.data)
        self.assertEqual(response5.data[0], e_msg)
        mock_snapshot.objects.filter(
            share=share, snap_type='admin').exists.return_value = False

        # delete a share that doesn't exist
        e_msg = 'Share id (invalid) does not exist.'
        response9 = self.client.delete('%s/invalid' % self.BASE_URL)
        self.assertEqual(response9.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response9.data)
        self.assertEqual(response9.data[0], e_msg)

    @mock.patch('storageadmin.views.share.Service')
    def test_delete2(self, mock_service):
        # happy path
        # create share
        data = {'sname': 'rootshare', 'pool': 'pool1', 'size': 100}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response.data['name'], 'rootshare')

        # Delete share
        mock_service.objects.get.side_effect = None
        response7 = self.client.delete('%s/rootshare' % self.BASE_URL)
        self.assertEqual(response7.status_code,
                         status.HTTP_200_OK, msg=response7.data)

    @mock.patch('storageadmin.views.share.Service')
    def test_delete3(self, mock_service):
        # unhappy path
        # create share
        data = {'sname': 'rootshare', 'pool': 'pool1', 'size': 100}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response.data['name'], 'rootshare')

        # Delete share
        e_msg = 'Failed to delete the share (rootshare). Error from the OS: '
        mock_service.objects.get.side_effect = None
        self.mock_remove_share.side_effect = Exception
        response7 = self.client.delete('%s/rootshare' % self.BASE_URL)
        self.assertEqual(response7.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response7.data)
        self.assertEqual(response7.data[0], e_msg)
        self.mock_remove_share.side_effect = None

        # Delete share that is in use by rock-on service
        class MockService(object):
            def __init__(self, **kwargs):
                self.config = {'root_share': 'rootshare', }
        e_msg = ('Share (rootshare) cannot be deleted because it is in use '
                 'by the Rock-on service. To override this block select '
                 'the force checkbox and try again.')
        mock_service.objects.get.side_effect = MockService
        response7 = self.client.delete('%s/rootshare' % self.BASE_URL)
        self.assertEqual(response7.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response7.data)
        self.assertEqual(response7.data[0], e_msg)
