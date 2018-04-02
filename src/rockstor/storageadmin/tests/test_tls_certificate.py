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


class TlscertificateTests(APITestMixin, APITestCase):
    fixtures = ['fix1.json']
    BASE_URL = '/api/certificates'

    @classmethod
    def setUpClass(cls):
        super(TlscertificateTests, cls).setUpClass()

        # post mocks

        cls.patch_move = patch('storageadmin.views.tls_certificate.move')
        cls.mock_move = cls.patch_move.start()

        cls.patch_superctl = patch('storageadmin.views.tls_certificate.superctl')  # noqa E501
        cls.mock_superctl = cls.patch_superctl.start()

        cls.patch_run_command = patch('storageadmin.views.tls_certificate.run_command')  # noqa E501
        cls.mock_run_command = cls.patch_run_command.start()

    @classmethod
    def tearDownClass(cls):
        super(TlscertificateTests, cls).tearDownClass()

    def test_get(self):

        # get base URL
        response = self.client.get(self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_post_requests(self):

        # TODO: add test where cert and key don't match ie triggering:
        # "Given Certificate and the Private Key do not match. ..."

        # invalid certificate and key
        self.mock_run_command.side_effect = Exception('openssl mock exception')
        data = {'name': 'cert1',
                'cert': '-----BEGIN CERTIFICATE-----MIIDXTCCAkWgAwIBAgIJAJC1HiIAZAiIMA0GCSqGSIb3DQEBBQUAMEUBAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnR----END CERTIFICATE-----',  # noqa E501
                'key': '-----BEGIN ENCRYPTED PRIVATE KEY----FDjBABgkqhkiG9w0BBQ0wMzAbBgkqhkiG9w0BBQwwDgQIS2qgprFqPxECAggA9g73NQbtqZwI+9X5OhpSg/2ALxlCCjbqvzgSu8gfFZ4yo+Xd8VucZDmDSpzZGDod---END ENCRYPTED PRIVATE KEY-----'}  # noqa E501
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)

        e_msg = ('RSA key modulus could not be verified for the given Private '
                 'Key. Correct your input and try again.')
        self.assertEqual(response.data[0], e_msg)

        # happy path
        # remove above moc exception
        self.mock_run_command.side_effect = None
        # and give clean (empty) outputs when called
        self.mock_run_command.return_value = ([''], [''], 0)
        data = {'name': 'cert1',
                'cert': '-----BEGIN CERTIFICATE-----MIIDXTCCAkWgAwIBAgIJAJC1HiIAZAiIMA0GCSqGSIb3DQEBBQUAMEUBAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnR----END CERTIFICATE-----',  # noqa E501
                'key': '-----BEGIN ENCRYPTED PRIVATE KEY----FDjBABgkqhkiG9w0BBQ0wMzAbBgkqhkiG9w0BBQwwDgQIS2qgprFqPxECAggA9g73NQbtqZwI+9X5OhpSg/2ALxlCCjbqvzgSu8gfFZ4yo+Xd8VucZDmDSpzZGDod---END ENCRYPTED PRIVATE KEY-----'}  # noqa E501
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
