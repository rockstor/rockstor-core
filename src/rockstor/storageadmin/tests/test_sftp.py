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

from storageadmin.models import Pool, Share, SFTP
from storageadmin.tests.test_api import APITestMixin


class SFTPTests(APITestMixin, APITestCase):
    # fixture with:
    # share-sftp (admin:admin) exported by SFTP
    # share-root-owned (root:root) - no SFTP export
    # share-user-owned (admin:admin) - no SFTP export.
    fixtures = ['test_sftp.json']
    BASE_URL = '/api/sftp'

    @classmethod
    def setUpClass(cls):
        super(SFTPTests, cls).setUpClass()

        # post mocks

        cls.patch_is_share_mounted = patch('storageadmin.views.sftp.'
                                           'is_share_mounted')
        cls.mock_is_share_mounted = cls.patch_is_share_mounted.start()
        cls.mock_is_share_mounted.return_value = True

        cls.patch_helper_mount_share = patch('storageadmin.views.sftp.'
                                             'helper_mount_share')
        cls.mock_helper_mount_share = cls.patch_helper_mount_share.start()
        cls.mock_helper_mount_share.return_value = True

        cls.patch_sftp_mount = patch('storageadmin.views.sftp.sftp_mount')
        cls.mock_sftp_mount = cls.patch_sftp_mount.start()
        cls.mock_sftp_mount.return_value = True

        # all values as per fixture
        cls.temp_pool = Pool(id=10, name='rock-pool', size=5242880)
        # the following line fails with: "Share matching query does not exist."
        # cls.temp_share_sftp = Share.objects.get(pk=18)
        cls.temp_share_sftp = Share(id=18, name='share-sftp',
                                    pool=cls.temp_pool, owner='admin',
                                    group='admin')
        cls.temp_share_root_owned = Share(id=19, name='share-root-owned',
                                          pool=cls.temp_pool)
        cls.temp_share_user_owned = Share(id=20, name='share-user-owned',
                                          pool=cls.temp_pool, owner='admin',
                                          group='admin')

        cls.temp_sftp = SFTP(id=1, share=cls.temp_share_sftp)

    @classmethod
    def tearDownClass(cls):
        super(SFTPTests, cls).tearDownClass()

    def test_get(self):
        """
        Test GET request
        1. Get base URL
        2. Get request with id
        """
        # get base URL
        self.get_base(self.BASE_URL)

        # get sftp with id
        response = self.client.get('{}/1'.format(self.BASE_URL))
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response)

    def test_post_requests_1(self):
        """
        invalid sftp operations
        1. Create sftp without providing share names
        """

        # create sftp with no share names
        data = {'read_only': 'true', }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = 'Must provide share names.'
        self.assertEqual(response.data[0], e_msg)

    # TODO: FAIL repair needed.
    @mock.patch('storageadmin.views.share_helpers.Share')
    def test_post_requests_2(self, mock_share):
        """
        . Create sftp for root-owned share
        . Create sftp for the share that is already exported
        . Create sftp for user-owned share
        """

        mock_share.objects.get.return_value = self.temp_share_root_owned

        # create sftp with share owned by root
        data = {'shares': ('share-root-owned',)}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Share (share-root-owned) is owned by root. It cannot be '
                 'exported via SFTP with root ownership.')
        self.assertEqual(response.data[0], e_msg)

        # TODO: the rest of this test fails with
        # 'Share matching query does not exist.'
        # and later:
        # AssertionError: "[Errno 2] No such file or directory:
        # '/lib64/libpopt.so.0'" != 'Share (share-sftp) is already exported via SFTP.'

        # mock_share.objects.get.return_value = self.temp_share_sftp
        #
        # # create sftp with already existing and sftp exported share.
        # data = {'shares': ('share-sftp',)}
        # response = self.client.post(self.BASE_URL, data=data)
        # self.assertEqual(response.status_code,
        #                  status.HTTP_500_INTERNAL_SERVER_ERROR,
        #                  msg=response.data)
        # e_msg = 'Share (share-sftp) is already exported via SFTP.'
        # self.assertEqual(response.data[0], e_msg)

        # # TODO: FAIL:
        # #  stderr = ["usermod: user \'admin\' does not exist", \'\']\n']
        # mock_share.objects.get.return_value = self.temp_share_user_owned
        #
        # # happy path
        # data = {'shares': ('share-user-owned',), 'read_only': 'true', }
        # response = self.client.post(self.BASE_URL, data=data)
        # self.assertEqual(response.status_code,
        #                  status.HTTP_200_OK, msg=response.data)

    def test_delete_requests_1(self):
        """
        1. Delete sftp export that does not exist
        """

        # Delete sftp that does not exists
        sftp_id = 99999
        response = self.client.delete('{}/{}'.format(self.BASE_URL, sftp_id))
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = 'SFTP config for the id ({}) does not exist.'.format(sftp_id)
        self.assertEqual(response.data[0], e_msg)

    @mock.patch('storageadmin.views.sftp.SFTP')
    def test_delete_requests_2(self, mock_sftp):
        """
        1. Delete sftp export
        """

        mock_sftp.objects.get.return_value = self.temp_sftp

        # happy path
        sftp_id = self.temp_sftp.id
        response = self.client.delete('{}/{}'.format(self.BASE_URL, sftp_id))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
