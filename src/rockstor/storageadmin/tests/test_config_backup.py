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
from storageadmin.tests.test_api import APITestMixin


class CongigBackupTests(APITestMixin, APITestCase):
    fixtures = ['fix2.json']
    BASE_URL = '/api/config-backup'

    @classmethod
    def setUpClass(cls):
        super(CongigBackupTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(CongigBackupTests, cls).tearDownClass()

    def test_valid_requests(self):
        # happy path POST
        response = self.client.post(self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # Happy path POST with restore command test restore .... backup with
        # id=1 is created when above post api call is made
        data = {'command': 'restore'}
        response = self.client.post('%s/1' % self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # Happy path DELETE
        response = self.client.delete('%s/1' % self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_config_upload_file(self):
        # happy path POST
        data = {'file-name': 'file1', 'file': 'file1 txt'}
        response = self.client.post('%s/file-upload' % self.BASE_URL,
                                    data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
