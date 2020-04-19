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
import mock
from rest_framework import status
from rest_framework.test import APITestCase
from mock import patch
from storageadmin.models import Pool, Share, NFSExportGroup, NFSExport
from storageadmin.tests.test_api import APITestMixin


class NFSExportTests(APITestMixin, APITestCase):
    # fixture with:
    # share-nfs - NFS exported - with defaults: client=*, Writable, async
    # {'host_str': '*', 'mod_choice': 'rw', 'sync_choice': 'async', }
    # share2 - no NFS export
    # fixtures = ['fix4.json']
    fixtures = ['test_nfs.json']
    BASE_URL = '/api/nfs-exports'

    @classmethod
    def setUpClass(cls):
        super(NFSExportTests, cls).setUpClass()

        # post mocks
        cls.patch_mount_share = patch('storageadmin.views.nfs_exports.'
                                      'mount_share')
        cls.mock_mount_share = cls.patch_mount_share.start()
        cls.mock_mount_share.return_value = ['out'], ['err'], 0

        cls.patch_refresh_nfs_exports = patch('storageadmin.views.nfs_exports.'
                                              'refresh_nfs_exports')
        cls.mock_refresh_nfs_exports = cls.patch_refresh_nfs_exports.start()
        cls.mock_refresh_nfs_exports.return_value = ['out'], ['err'], 0

        # potential mocks for NFSExportGroup
        # validate_nfs_host_str
        # validate_nfs_modify_str
        # validate_nfs_sync_choice

        # all values as per fixture
        cls.temp_pool = Pool(id=11, name='rock-pool', size=5242880)
        cls.temp_share_nfs = Share(id=21, name='share-nfs', pool=cls.temp_pool)
        # the following is not picking up from db !!
        # cls.temp_nfsexportgroup = NFSExportGroup.objects.get(id=1)
        cls.temp_nfsexportgroup = NFSExportGroup(id=1)
        cls.temp_nfsexport = NFSExport(export_group=cls.temp_nfsexportgroup,
                                       share=cls.temp_share_nfs,
                                       mount='/export/share-nfs', id=1)

        cls.temp_share2 = Share(id=22, name='share2', pool=cls.temp_pool)

    @classmethod
    def tearDownClass(cls):
        super(NFSExportTests, cls).tearDownClass()

    # TODO: FAIL {"detail":"Not found."}
    # def test_get(self):
    #     """
    #     Test GET request
    #     1. Get base URL
    #     2. Get request with id
    #     """
    #     # get base URL
    #     self.get_base(self.BASE_URL)
    #
    #     # get nfs-export with id
    #     nfs_id = self.temp_nfsexport.id
    #     response = self.client.get('{}/{}'.format(self.BASE_URL, nfs_id))
    #     self.assertEqual(response.status_code, status.HTTP_200_OK,
    #                      msg=response)

    def test_invalid_get(self):
        # get nfs-export with invalid id
        response = self.client.get('{}/99999'.format(self.BASE_URL))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND,
                         msg=response)

    @mock.patch('storageadmin.views.share_helpers.Share')
    def test_post_requests(self, mock_share):
        """
        invalid nfs-export api operations
        1. Add nfs-export without providing share names
        2  Add nfs-export
        3. Add nfs-export for the share that has already been exported

        """

        # Add nfs-export without providing share names
        self.mock_refresh_nfs_exports.side_effect = None
        self.mock_refresh_nfs_exports.return_value = 'out', 'err', 0

        data = {'host_str': '*', 'mod_choice': 'rw', 'sync_choice': 'async', }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = 'Cannot export without specifying shares.'
        self.assertEqual(response.data[0], e_msg)

        mock_share.objects.get.return_value = self.temp_share2

        # AssertionError: ["{'share': [u'share instance with id 22 does not exist.']}",
        # # happy path
        # data1 = {'shares': ('share2',), 'host_str': '*.edu',
        #          'mod_choice': 'rw', 'sync_choice': 'async', }
        # response = self.client.post(self.BASE_URL, data=data1)
        # self.assertEqual(response.status_code,
        #                  status.HTTP_200_OK, msg=response.data)

        # # Add nfs-export for the share that is already been exported
        # data1 = {'shares': ('share1',), 'host_str': '*', 'mod_choice': 'rw',
        #          'sync_choice': 'async', }
        # response = self.client.post(self.BASE_URL, data=data1)
        # self.assertEqual(response.status_code,
        #                  status.HTTP_500_INTERNAL_SERVER_ERROR,
        #                  msg=response.data)
        # e_msg = 'An export already exists for the host string: (*).'
        # self.assertEqual(response.data[0], e_msg)

        # Add nfs-export with invalid nfs-client
        data1 = {'shares': ('share1',), 'host_str': '*', 'mod_choice': 'rw',
                 'sync_choice': 'async', }
        response = self.client.post(self.BASE_URL, data=data1)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        # TODO: AssertionError: "{'share': [u'share instance with id 22 does not exist.']}
        # e_msg = 'An export already exists for the host string: (*).'
        # self.assertEqual(response.data[0], e_msg)

    # TODO: Test needs updating
    #  AssertionError: ['Share with name (clone1) does not exist.',
    # def test_no_nfs_client(self):
    #     # Add nfs-export without specifying nfs-clients(host string). The
    #     # server side defaults the host string to * so test for this.
    #
    #     self.mock_refresh_nfs_exports.side_effect = None
    #     data1 = {'shares': ('clone1',), 'mod_choice': 'rw',
    #              'sync_choice': 'async', }
    #     response = self.client.post(self.BASE_URL, data=data1)
    #     self.assertEqual(response.status_code,
    #                      status.HTTP_200_OK, msg=response.data)
    #     self.assertEqual(response.data['host_str'], '*')

    # def test_invalid_nfs_client2(self):
    #
    #     # TODO: Test needs updating
    #     # invalid post request
    #     # Add nfs-export providing invalid nfs client
    #     self.mock_refresh_nfs_exports.side_effect = Exception()
    #
    #     data1 = {'shares': ('clone1',), 'host_str': 'host%%%edu',
    #              'mod_choice': 'rw', 'sync_choice': 'async', }
    #     response = self.client.post(self.BASE_URL, data=data1)
    #     self.assertEqual(response.status_code,
    #                      status.HTTP_500_INTERNAL_SERVER_ERROR,
    #                      msg=response.data)
    #
    #     e_msg = 'Invalid Hostname or IP: host%%%edu'
    #     self.assertEqual(response.data[0], e_msg)
    #     self.mock_refresh_nfs_exports.side_effect = None
    #
    # def test_invalid_nfs_client3(self):
    #
    #     # TODO: Test needs updating
    #     # invalid put request
    #     # edit nfs-export providing invalid nfs-client
    #     self.mock_refresh_nfs_exports.side_effect = Exception()
    #     nfs_id = 11
    #     data = {'shares': ('share2',), 'host_str': 'host%%%edu',
    #             'admin_host': ' ', 'mod_choice': 'rw',
    #             'sync_choice': 'async', }
    #     response = self.client.put('{}/{}'.format(self.BASE_URL, nfs_id),
    #                                data=data)
    #     self.assertEqual(response.status_code,
    #                      status.HTTP_500_INTERNAL_SERVER_ERROR,
    #                      msg=response.data)
    #     e_msg = 'Invalid Hostname or IP: host%%%edu'
    #     self.assertEqual(response.data[0], e_msg)
    #     self.mock_refresh_nfs_exports.side_effect = None

    @mock.patch('storageadmin.views.share_helpers.Share')
    def test_invalid_admin_host1(self, mock_share):

        mock_share.objects.get.return_value = self.temp_share2

        # invalid post request
        # Add nfs-export providing invalid admin host
        self.mock_refresh_nfs_exports.side_effect = Exception()
        data = {'shares': ('share2',), 'host_str': '*.edu',
                'admin_host': 'admin%host', 'mod_choice': 'rw',
                'sync_choice': 'async', }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        # TODO: FAIL AssertionError:
        #  "{'share': [u'share instance with id 22 does not exist.']}"
        #  != 'Invalid admin host: admin%host'
        # e_msg = 'Invalid admin host: admin%host'
        # self.assertEqual(response.data[0], e_msg)
        self.mock_refresh_nfs_exports.side_effect = None

    def test_invalid_admin_host2(self):
        # invalid put request
        # edit nfs-export providing invalid admin host
        self.mock_refresh_nfs_exports.side_effect = Exception()
        nfs_id = 11
        data = {'shares': ('share2',), 'host_str': '*.edu',
                'admin_host': 'admin%host', 'mod_choice': 'rw',
                'sync_choice': 'async', }
        response = self.client.put('{}/{}'.format(self.BASE_URL, nfs_id),
                                   data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        # TODO: FAIL AssertionError:
        #  'Share with name (share2) does not exist.' != 'Invalid admin host: admin%host'
        # e_msg = 'Invalid admin host: admin%host'
        # self.assertEqual(response.data[0], e_msg)
        self.mock_refresh_nfs_exports.side_effect = None

    @mock.patch('storageadmin.views.nfs_exports.NFSExportGroup')
    @mock.patch('storageadmin.views.share_helpers.Share')
    def test_put_requests(self, mock_share, mock_nfsexportgroup):
        """
        . Edit nfs-export with no shares
        . Edit nfs-export
        . Edit nfs-export that does not exists
        """

        # Edit nfs-export with no shares
        self.mock_refresh_nfs_exports.side_effect = None
        self.mock_refresh_nfs_exports.return_value = 'out', 'err', 0

        nfs_id = self.temp_nfsexport.id
        data = {'host_str': '*.edu', 'mod_choice': 'rw',
                'sync_choice': 'async', }
        response = self.client.put('{}/{}'.format(self.BASE_URL, nfs_id),
                                   data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = 'Cannot export without specifying shares.'
        self.assertEqual(response.data[0], e_msg)

        mock_share.objects.get.return_value = self.temp_share_nfs
        mock_nfsexportgroup.objects.get.return_value = self.temp_nfsexportgroup

        # TODO: FAIL AssertionError: ["{'export_group': [u'This field cannot be null.'],
        #  'share': [u'share instance with id 21 does not exist.']}",
        # # happy path of editing existing nfs export
        # nfs_id = self.temp_nfsexport.id
        # data = {'shares': ('share-nfs',), 'host_str': '*.edu',
        #         'mod_choice': 'rw', 'sync_choice': 'async', }
        # response = self.client.put('{}/{}'.format(self.BASE_URL, nfs_id),
        #                            data=data)
        # self.assertEqual(response.status_code,
        #                  status.HTTP_200_OK, msg=response.data)

        # TODO: FAIL AssertionError: ["{'export_group': [u'This field cannot be null.'],
        #  'share': [u'share instance with id 21 does not exist.']}",
        # # happy path2 with admin host
        # nfs_id = 11
        # data = {'shares': ('share2',), 'host_str': '*.edu',
        #         'admin_host': 'host', 'mod_choice': 'rw',
        #         'sync_choice': 'async', }
        # response = self.client.put('{}/{}'.format(self.BASE_URL, nfs_id),
        #                            data=data)
        # self.assertEqual(response.status_code,
        #                  status.HTTP_200_OK, msg=response.data)

        # TODO: FAIL AssertionError: "{'export_group': [u'This field cannot be null.'],
        #  'share': [u'share instance with id 21 does not exist.']}"
        # # edit nfs-export that does not exist
        # nfs_id = 99999
        # data = {'shares': ('share2',), 'host_str': '*.edu',
        #         'mod_choice': 'rw', 'sync_choice': 'async', }
        # response = self.client.put('{}/{}'.format(self.BASE_URL, nfs_id),
        #                            data=data)
        # self.assertEqual(response.status_code,
        #                  status.HTTP_500_INTERNAL_SERVER_ERROR,
        #                  msg=response.data)
        # e_msg = 'NFS export with id ({}) does not exist.'.format(nfs_id)
        # self.assertEqual(response.data[0], e_msg)

    @mock.patch('storageadmin.views.nfs_exports.NFSExport')
    @mock.patch('storageadmin.views.nfs_exports.NFSExportGroup')
    def test_delete_requests(self, mock_nfsexportgroup, mock_nfsexport):

        """
        . Delete nfs-export that does not exist
        . Delete nfs-export
        """

        mock_nfsexportgroup.objects.get.return_value = self.temp_nfsexportgroup
        mock_nfsexport.objects.get.return_value = self.temp_nfsexport

        # happy path
        nfs_id = self.temp_nfsexport.id
        response = self.client.delete('{}/{}'.format(self.BASE_URL, nfs_id))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # TODO: FAIL
        # mock_nfsexport.objects.get.side_effect = NFSExport.DoesNotExist
        #
        # # Delete nfs-export that does nor exists
        # nfs_id = 99999
        # response = self.client.delete('{}/{}'.format(self.BASE_URL, nfs_id))
        # self.assertEqual(response.status_code,
        #                  status.HTTP_500_INTERNAL_SERVER_ERROR,
        #                  msg=response.data)
        # e_msg = 'NFS export with id ({}) does not exist.'.format(nfs_id)
        # self.assertEqual(response.data[0], e_msg)

    def test_adv_nfs_get(self):
        """
        Test GET request
        1. Get base URL
        2. Get request with id
        """
        # get base URL
        self.get_base('/api/adv-nfs-exports')

    @mock.patch('storageadmin.views.share_helpers.Share')
    def test_adv_nfs_post_requests(self, mock_share):

        mock_share.objects.get.return_value = self.temp_share_nfs

        # without specifying entries
        data = {}
        response = self.client.post('/api/adv-nfs-exports', data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = 'Cannot export without specifying entries.'
        self.assertEqual(response.data[0], e_msg)

        # happy path
        data = {'entries': ["/export/share-nfs *(rw,async,insecure)"]}
        response = self.client.post('/api/adv-nfs-exports', data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # Invalid entries
        data = {'entries': ["/export/share2"]}
        response = self.client.post('/api/adv-nfs-exports', data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = 'Invalid exports input -- (/export/share2).'
        self.assertEqual(response.data[0], e_msg)

        # Invalid entries
        data = {'entries': ["/export/share2 *(rw,async,insecure"]}
        response = self.client.post('/api/adv-nfs-exports', data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Invalid exports input -- (/export/share2 *(rw,async,'
                 'insecure). Offending section: (*(rw,async,insecure).')
        self.assertEqual(response.data[0], e_msg)

        # Invalid entries
        data = {'entries': ['invalid']}
        response = self.client.post('/api/adv-nfs-exports', data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = 'Invalid exports input -- (invalid).'
        self.assertEqual(response.data[0], e_msg)
