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


class SFTPTests(APITestMixin, APITestCase):
    fixtures = ['fix2.json']
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
        response = self.client.get('%s/4' % self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response)

    def test_post_requests(self):
        """
        invalid sftp operations
        1. Create sftp without providing share names
        2. Create a sftp for the share that is already been exported
        """

        # create sftp with no share names
        data = {'read_only': 'true', }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)

        e_msg = ('Must provide share names')
        self.assertEqual(response.data['detail'], e_msg)

        # create sftp with already existing share
        data = {'shares': ('share2',)}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)

        e_msg = ('Share(share2) is already exported via SFTP')
        self.assertEqual(response.data['detail'], e_msg)

        # create sftp with share owned by root
        data = {'shares': ('share1',)}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)

        e_msg = ('Share(share1) is owned by root. It cannot be exported via '
                 'SFTP with root ownership')
        self.assertEqual(response.data['detail'], e_msg)

        # happy path
        data = {'shares': ('share3',), 'read_only': 'true', }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_delete_requests(self):
        """
        1. Delete sftp that does not exist
        2. Delete sftp
        """
        # Delete sftp that does not exists
        sftp_id = 1
        response = self.client.delete('%s/%d' % (self.BASE_URL, sftp_id))
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('SFTP config for the id(1) does not exist')
        self.assertEqual(response.data['detail'], e_msg)

        # happy path
        sftp_id = 4
        response = self.client.delete('%s/%d' % (self.BASE_URL, sftp_id))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
