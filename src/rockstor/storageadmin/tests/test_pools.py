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


class PoolTests(APITestCase):
    fixtures = ['pool.json']
    BASE_URL = '/api/pools'

    def session_login(self):
        self.client.login(username='admin', password='admin')

    def test_pools_0(self):
        """
        unauthorized api access
        """
        response = self.client.get(self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_pools_1(self):
        """
        raid0 tests
        """
        self.session_login()
        data = {'disks': ('sdb', 'sdc',),
                'pname': 'raid0pool',
                'raid_level': 'raid0', }

        #create
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response.data['name'], 'raid0pool')
        #add disks
        data2 = {'disks': ('sdd', 'sde',), }
        response2 = self.client.put('%s/raid0pool/add' % self.BASE_URL,
                                    data=data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK,
                         msg=response2.data)
        self.assertEqual(len(response2.data['disks']), 4)
        #remove disk
        data3 = {'disk': ('sde',), }
        response3 = self.client.put('%s/raid0pool/remove' % self.BASE_URL,
                                    data=data3)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response3.data)
        #delete
        response4 = self.client.delete('%s/raid0pool' % self.BASE_URL)
        self.assertEqual(response4.status_code, status.HTTP_200_OK,
                         msg=response4.data)

    def test_pool_1_1(self):
        """
        raid0 with one disk
        """
        self.session_login()
        data = {'disks': ('sdb',),
                'pname': 'raid0pool',
                'raid_level': 'raid0', }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data['detail'], 'More than one disk is '
                         'required for the raid level: raid0')

    def test_pools_2(self):
        """
        raid1 with num disks != 2
        """
        self.session_login()
        data = {'disks': ('sdb',),
                'pname': 'raid1pool',
                'raid_level': 'raid1', }
        e_msg = ('Exactly two disks are required for the raid level: raid1')
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)
        data['disks'] = ('sdb', 'sdc', 'sdd',)
        response2 = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response2.data)
        self.assertEqual(response2.data['detail'], e_msg)

    def test_pools_2_1(self):
        """
        raid1 tests
        """
        self.session_login()
        data = {'disks': ('sdb', 'sdc',),
                'pname': 'raid1pool',
                'raid_level': 'raid1', }

        #create
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response.data['name'], 'raid1pool')
        #add disks
        data2 = {'disks': ('sdd', 'sde',), }
        response2 = self.client.put('%s/raid1pool/add' % self.BASE_URL,
                                    data=data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK,
                         msg=response2.data)
        self.assertEqual(len(response2.data['disks']), 4)
        #remove disk
        data3 = {'disk': ('sde',), }
        response3 = self.client.put('%s/raid1pool/remove' % self.BASE_URL,
                                    data=data3)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response3.data)
        #delete
        response4 = self.client.delete('%s/raid1pool' % self.BASE_URL)
        self.assertEqual(response4.status_code, status.HTTP_200_OK,
                         msg=response4.data)

    def _test_pools_3(self):
        """
        raid10 tests
        """
        self.session_login()
        data = {'disks': ('sdb', 'sdc', 'sdd', 'sde',),
                'pname': 'raid1pool',
                'raid_level': 'raid1', }

        #create
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response.data['name'], 'raid1pool')
        #add disks
        data2 = {'disks': ('sdd', 'sde',), }
        response2 = self.client.put('%s/raid1pool/add' % self.BASE_URL,
                                    data=data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK,
                         msg=response2.data)
        self.assertEqual(len(response2.data['disks']), 4)
        #remove disk
        data3 = {'disk': ('sde',), }
        response3 = self.client.put('%s/raid1pool/remove' % self.BASE_URL,
                                    data=data3)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response3.data)
        #delete
        response4 = self.client.delete('%s/raid1pool' % self.BASE_URL)
        self.assertEqual(response4.status_code, status.HTTP_200_OK,
                         msg=response4.data)

    def _test_pools_4(self):
        """
        raid5 tests
        """
        self.session_login()

    def _test_pools_5(self):
        """
        raid6 tests
        """
        self.session_login()
