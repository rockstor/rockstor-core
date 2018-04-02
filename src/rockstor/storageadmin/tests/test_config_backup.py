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
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

import storageadmin
from storageadmin.models import ConfigBackup
from storageadmin.tests.test_api import APITestMixin


class ConfigBackupTests(APITestMixin, APITestCase):
    fixtures = ['fix2.json']
    BASE_URL = '/api/config-backup'

    @classmethod
    def setUpClass(cls):
        super(ConfigBackupTests, cls).setUpClass()

        # TODO: may need to mock os.path.isfile

    @classmethod
    def tearDownClass(cls):
        super(ConfigBackupTests, cls).tearDownClass()

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

    # TODO: 'module' object has no attribute 'views'
    # when attempting to mock uploaded file content.
    # @mock.patch(storageadmin.views.config_backup.ConfigBackup)
    # def test_config_upload_file(self, mock_config_backup):
    #
    #     # happy path POST
    #     # so the following test throws:
    #     # 'FileUpload parse error - none of upload handlers can handle the
    #     # stream'
    #
    #     # we use a SimpleUploadedFile Object to act as our
    #     # ConfigBackup.config_backup (a models.fileField)
    #
    #     # setup fake zip file as models.FileField substitute in ConfigBackup
    #     fake_file = SimpleUploadedFile('file1.txt', b"fake-file-contents",
    #                                    content_type="application/zip")
    #
    #     # TODO: We also need to setup a content_type='text/plain' to test
    #     # failure when file is not a zip file.
    #
    #     # override "config_backup = models.FileField" in super
    #     class MockConfigBackup(ConfigBackup):
    #         def __init__(self, **kwargs):
    #             self.config_backup = \
    #                 SimpleUploadedFile(self.filename, b"fake-file-contents",
    #                                    content_type="application/zip")
    #
    #         def save(self):
    #             pass
    #
    #     mock_config_backup.objects.get.side_effect = MockConfigBackup
    #
    #
    #     data = {'file-name': 'file1', 'file': 'file1.txt'}
    #     response = self.client.post('%s/file-upload' % self.BASE_URL,
    #                                 data=data)
    #     self.assertEqual(response.status_code,
    #                      status.HTTP_200_OK, msg=response.data)

