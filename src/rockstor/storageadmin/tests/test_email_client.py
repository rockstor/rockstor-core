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
from system.services import systemctl
import mock
from mock import patch
from storageadmin.tests.test_api import APITestMixin

class EmailTests(APITestMixin, APITestCase):
    fixtures = ['fix2.json']
    BASE_URL = '/api/email'

    @classmethod
    def setUpClass(cls):
        super(EmailTests, cls).setUpClass()


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
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)

        e_msg = 'unknown command(send-email) is not supported.'
        self.assertEqual(response.data['detail'], e_msg)
       
        # send test email before setting up email account
        response = self.client.post('%s/send-test-email' % self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)

        e_msg = 'E-mail account must be setup first before test e-mail could be sent'
        self.assertEqual(response.data['detail'], e_msg)
        
        
        # happy path
        data = {'name':'Tester', 'smtp_server':'smtp.gmail.com' , 'password': 'password', 'sender': 'mchakravartula@gmail.com', 'receiver': 'mchakravartula@gmail.com'}
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