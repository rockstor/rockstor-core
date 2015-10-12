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
from rest_framework.response import Response
from rest_framework.test import APITestCase
import mock
from mock import patch
from storageadmin.tests.test_api import APITestMixin

class DiskSmartTests(APITestMixin, APITestCase):
    fixtures = ['fix3.json']
    BASE_URL = '/api/disks/smart'

    @classmethod
    def setUpClass(cls):
        super(DiskSmartTests, cls).setUpClass()

        # post mocks
        


    @classmethod
    def tearDownClass(cls):
        super(DiskSmartTests, cls).tearDownClass()

    def test_get(self):
    
        # invalid disk
        invalid_disk = 'invalid'
        response = self.client.get('%s/%s/%s' % (self.BASE_URL,'info',invalid_disk))
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ('Disk: invalid does not exist')
        self.assertEqual(response.data['detail'], e_msg)

        # happy path
        disk_name = 'sdd'
        response = self.client.get('%s/%s/%s' % (self.BASE_URL,'info',disk_name))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
        

    def test_post_requests(self):  
    
        # invalid test_type in test command 
        disk_name = 'sdd'
        data = {'test_type':'invalid_test'}
        response = self.client.post('%s/%s/%s' % (self.BASE_URL, 'test', disk_name),data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ('Unsupported Self-Test: invalid_test')
        self.assertEqual(response.data['detail'], e_msg)                 
                         
        # invalid command 
        disk_name = 'sdd'
        invalid_command = 'invalid'
        response = self.client.post('%s/%s/%s' % (self.BASE_URL, invalid_command, disk_name))
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ('Unknown command: invalid. Only valid commands are info and test')
        self.assertEqual(response.data['detail'], e_msg)                
                         
        # happy path 
        disk_name = 'sdd'
        response = self.client.post('%s/%s/%s' % (self.BASE_URL, 'info', disk_name))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
                 
    