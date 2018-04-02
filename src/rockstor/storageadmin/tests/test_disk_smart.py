
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

from storageadmin.models import Disk
from storageadmin.tests.test_api import APITestMixin


class DiskSmartTests(APITestMixin, APITestCase):
    fixtures = ['fix1.json']
    BASE_URL = '/api/disks/smart'

    @classmethod
    def setUpClass(cls):
        super(DiskSmartTests, cls).setUpClass()

        # post mocks
        cls.patch_extended_info = patch(
            'storageadmin.views.disk_smart.extended_info')
        cls.mock_extended_info = cls.patch_extended_info.start()

        cls.patch_capabilities = patch(
            'storageadmin.views.disk_smart.capabilities')
        cls.mock_capabilities = cls.patch_capabilities.start()

        cls.patch_info = patch('storageadmin.views.disk_smart.info')
        cls.mock_info = cls.patch_info.start()

        cls.patch_error_logs = patch(
            'storageadmin.views.disk_smart.error_logs')
        cls.mock_error_logs = cls.patch_error_logs.start()
        cls.mock_error_logs.return_value = {}, []

        cls.patch_test_logs = patch('storageadmin.views.disk_smart.test_logs')
        cls.mock_test_logs = cls.patch_test_logs.start()
        cls.mock_test_logs.return_value = {}, []

        cls.patch_run_test = patch('storageadmin.views.disk_smart.run_test')
        cls.mock_run_test = cls.patch_run_test.start()
        cls.mock_run_test.return_value = [''], [''], 0

        cls.temp_disk = Disk(id=2, name='mock-disk', size=88025459,
                             parted=False)

    @classmethod
    def tearDownClass(cls):
        super(DiskSmartTests, cls).tearDownClass()

    @mock.patch('storageadmin.views.disk_smart.Disk')
    def test_get(self, mock_disk):

        # TODO: Don't think "api/disks/smart" is meant to work.
        # get base URL
        # response = self.client.get('{}'.format(self.BASE_URL))
        # self.assertEqual(response.status_code,
        #                  status.HTTP_200_OK, msg=response.data)

        mock_disk.objects.get.return_value = self.temp_disk

        # get with disk id
        response = self.client.get('{}/info/1'.format(self.BASE_URL))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_post_reqeusts_1(self):

        # # invalid disk id
        diskId = 99999
        response = self.client.post('{}/info/{}'.format(self.BASE_URL, diskId))
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = 'Disk id ({}) does not exist.'.format(diskId)
        self.assertEqual(response.data[0], e_msg)

    @mock.patch('storageadmin.views.disk_smart.Disk')
    def test_post_requests_2(self, mock_disk):

        # invalid command
        diskId = 2
        response = self.client.post('{}/invalid/{}'.format(self.BASE_URL,
                                                           diskId))
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Unknown command: (invalid). The only valid commands are '
                 'info and test.')
        self.assertEqual(response.data[0], e_msg)

        # unsupported self test
        data = {'test_type': 'invalid'}
        response = self.client.post('{}/test/{}'.format(self.BASE_URL, diskId),
                                    data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = 'Unsupported Self-Test: (invalid).'
        self.assertEqual(response.data[0], e_msg)

        mock_disk.objects.get.return_value = self.temp_disk

        # test command
        data = {'test_type': 'short'}
        response = self.client.post('{}/test/{}'.format(self.BASE_URL, diskId),
                                    data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # happy path
        response = self.client.post('{}/info/{}'.format(self.BASE_URL, diskId))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
