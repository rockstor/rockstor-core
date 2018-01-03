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


class EmailTests(APITestMixin, APITestCase):
    fixtures = ['fix2.json']
    BASE_URL = '/api/email'

    @classmethod
    def setUpClass(cls):
        super(EmailTests, cls).setUpClass()

        cls.patch_systemctl = patch(
            'storageadmin.views.email_client.systemctl')
        cls.mock_systemctl = cls.patch_systemctl.start()

        cls.patch_send_test_email = patch(
            'storageadmin.views.email_client.send_test_email')
        cls.mock_send_test_email = cls.patch_send_test_email.start()

        cls.patch_update_postfix = patch(
            'storageadmin.views.email_client.update_postfix')
        cls.mock_update_postfix = cls.patch_update_postfix.start()

        cls.patch_update_generic = patch(
            'storageadmin.views.email_client.update_generic')
        cls.mock_update_generic = cls.patch_update_generic.start()

        cls.patch_update_forward = patch(
            'storageadmin.views.email_client.update_forward')
        cls.mock_update_forward = cls.patch_update_forward.start()

        cls.patch_update_sasl = patch(
            'storageadmin.views.email_client.update_sasl')
        cls.mock_update_sasl = cls.patch_update_sasl.start()

    @classmethod
    def tearDownClass(cls):
        super(EmailTests, cls).tearDownClass()

    def test_get(self):
        """
        Test GET request
        1. Get base URL
        2. Get request with id
        """
        # get base URL
        self.client.get(self.BASE_URL)

    def test_post_requests(self):
        # unknown command
        response = self.client.post('%s/send-email' % self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)

        e_msg = 'Unknown command (send-email) is not supported.'
        self.assertEqual(response.data['detail'], e_msg)

        # send test email before setting up email account
        response = self.client.post('%s/send-test-email' % self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)

        e_msg = ('E-mail account must be setup before a '
                 'test e-mail can be sent.')
        self.assertEqual(response.data['detail'], e_msg)

        # happy path
        data = {'name': 'Tester', 'smtp_server': 'smtp.gmail.com',
                'password': 'password', 'sender': 'mchakravartula@gmail.com',
                'receiver': 'mchakravartula@gmail.com'}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # test 'send-test-email'
        response = self.client.post('%s/send-test-email' % self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_delete_requests(self):
        # happy path
        response = self.client.delete(self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
