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
import mock
from storageadmin.models import Pool


class PoolTests(APITestCase):
    fixtures = ['fix1.json']
    BASE_URL = '/api/pools'

    def session_login(self):
        self.client.login(username='admin', password='admin')

    def test_pools_auth(self):
        """
        unauthorized api access
        """
        response = self.client.get(self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # patches for put
    @mock.patch('storageadmin.views.pool.resize_pool')
    @mock.patch('storageadmin.views.pool.balance_start')
    # patches for post
    @mock.patch('storageadmin.views.pool.mount_root')
    @mock.patch('storageadmin.views.pool.add_pool')
    @mock.patch('storageadmin.views.pool.pool_usage')
    @mock.patch('storageadmin.views.pool.btrfs_uuid')
    def test_pools_raid0_crud(self, mock_btrfs_uuid, mock_pool_usage, mock_add_pool,
                              mock_mount_root, mock_balance_start, mock_resize_pool):
        """
        raid0 CRUD api tests
        """
        self.session_login()
        data = {'disks': ('sdb', 'sdc',),
                'pname': 'raid0pool',
                'raid_level': 'raid0', }

        # post mocks
        mock_btrfs_uuid.return_value = 'bar'
        mock_pool_usage.return_value = (100, 10, 90)
        mock_add_pool.return_value = True
        mock_mount_root.return_value = 'foo'

        #create (test post)
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data['name'], 'raid0pool')
        self.assertEqual(response.data['raid'], 'raid0')
        # TODO confirm with Suman this is correct... post should save disks?
        # disk assert was failing... list is 'empty'... post function was not adding disks to the pool (atleast not saving them)... appears they WERE added but then dropped it on DB call
        # not sure what is supposed to add the disks to the pool.. "p.disk_set.add(*disks)" line 195?
        # solution: assigned disks to the pool & saved each disk
        # sure that one of the mocked methods doesen't handle this?
        self.assertEqual(len(response.data['disks']), 2)

        # add disks (test put)
        data2 = {'disks': ('sdd', 'sde',), }

        # TODO.. worth testing for exception raises? e.g. empty disks
        # data2 = {'disks': (), }

        mock_balance_start.return_value = 1
        response2 = self.client.put('%s/raid0pool/add' % self.BASE_URL, data=data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK, msg=response2.data)
        self.assertEqual(len(response2.data['disks']), 4)

        #remove disk (test put)
        # TODO check why this should return a 500 error?
        data3 = {'disk': ('sde',), }
        response3 = self.client.put('%s/raid0pool/remove' % self.BASE_URL, data=data3)
        self.assertEqual(response3.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response3.data)
        # self.assertEqual(len(response3.data['disks']), 3)
        # print response3.data
        # print dir(response3.data)

        #delete
        response4 = self.client.delete('%s/raid0pool' % self.BASE_URL)
        self.assertEqual(response4.status_code, status.HTTP_200_OK, msg=response4.data)
        # TODO benefit to checking object is actually deleted? Or is that considered testing django ORM?
        # self.assertRaises(Exception, Pool.objects.get(name='raid0pool'))
        # self.assertRaises(DoesNotExist, Pool.objects.get(name='raid0pool'))

        # todo test get?
        # response5 = self.client.get(self.BASE_URL)
        # self.assertEqual(response5.status_code, status.HTTP_200_OK, msg=response5.data)
        # print response5.data
        # print dir(response5.data)
        # self.assertEqual(len(response5.data['results'][0]['disks']), 1)

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

    # patches for post
    @mock.patch('storageadmin.views.pool.mount_root')
    @mock.patch('storageadmin.views.pool.add_pool')
    @mock.patch('storageadmin.views.pool.pool_usage')
    @mock.patch('storageadmin.views.pool.btrfs_uuid')
    # TODO organize tests by API call (i.e. all posts together?)
    def test_pools_2(self, mock_btrfs_uuid, mock_pool_usage, mock_add_pool, mock_mount_root):
        """
        raid1 with num disks check. must be >= 2
        """
        # post mocks
        mock_btrfs_uuid.return_value = 'bar'
        mock_pool_usage.return_value = (100, 10, 90)
        mock_add_pool.return_value = True
        mock_mount_root.return_value = 'foo'

        # test 1 disk fails
        self.session_login()
        data = {'disks': ('sdb',),
                'pname': 'raid1pool',
                'raid_level': 'raid1', }
        e_msg = ('At least two disks are required for the raid level: raid1')
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)

        # test 2 disks pass
        data['disks'] = ('sdb', 'sdc',)
        response2 = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response2.status_code, status.HTTP_200_OK, msg=response2.data)
        self.assertEqual(response2.data['name'], 'raid1pool')
        self.assertEqual(response2.data['raid'], 'raid1')
        self.assertEqual(len(response2.data['disks']), 2)


    # def test_pools_2_1(self):
    #     """
    #     raid1 tests
    #     """
    #     self.session_login()
    #     data = {'disks': ('sdb', 'sdc',),
    #             'pname': 'raid1pool',
    #             'raid_level': 'raid1', }
    #
    #     #create
    #     response = self.client.post(self.BASE_URL, data=data)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK,
    #                      msg=response.data)
    #     self.assertEqual(response.data['name'], 'raid1pool')
    #     #add disks
    #     data2 = {'disks': ('sdd', 'sde',), }
    #     response2 = self.client.put('%s/raid1pool/add' % self.BASE_URL,
    #                                 data=data2)
    #     self.assertEqual(response2.status_code, status.HTTP_200_OK,
    #                      msg=response2.data)
    #     self.assertEqual(len(response2.data['disks']), 4)
    #     #remove disk
    #     data3 = {'disk': ('sde',), }
    #     response3 = self.client.put('%s/raid1pool/remove' % self.BASE_URL,
    #                                 data=data3)
    #     self.assertEqual(response3.status_code,
    #                      status.HTTP_500_INTERNAL_SERVER_ERROR,
    #                      msg=response3.data)
    #     #delete
    #     response4 = self.client.delete('%s/raid1pool' % self.BASE_URL)
    #     self.assertEqual(response4.status_code, status.HTTP_200_OK,
    #                      msg=response4.data)
    #
    # def _test_pools_3(self):
    #     """
    #     raid10 tests
    #     """
    #     self.session_login()
    #     data = {'disks': ('sdb', 'sdc', 'sdd', 'sde',),
    #             'pname': 'raid1pool',
    #             'raid_level': 'raid1', }
    #
    #     #create
    #     response = self.client.post(self.BASE_URL, data=data)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK,
    #                      msg=response.data)
    #     self.assertEqual(response.data['name'], 'raid1pool')
    #     #add disks
    #     data2 = {'disks': ('sdd', 'sde',), }
    #     response2 = self.client.put('%s/raid1pool/add' % self.BASE_URL,
    #                                 data=data2)
    #     self.assertEqual(response2.status_code, status.HTTP_200_OK,
    #                      msg=response2.data)
    #     self.assertEqual(len(response2.data['disks']), 4)
    #     #remove disk
    #     data3 = {'disk': ('sde',), }
    #     response3 = self.client.put('%s/raid1pool/remove' % self.BASE_URL,
    #                                 data=data3)
    #     self.assertEqual(response3.status_code,
    #                      status.HTTP_500_INTERNAL_SERVER_ERROR,
    #                      msg=response3.data)
    #     #delete
    #     response4 = self.client.delete('%s/raid1pool' % self.BASE_URL)
    #     self.assertEqual(response4.status_code, status.HTTP_200_OK,
    #                      msg=response4.data)
    #
    # def _test_pools_4(self):
    #     """
    #     raid5 tests
    #     """
    #     self.session_login()
    #
    # def _test_pools_5(self):
    #     """
    #     raid6 tests
    #     """
    #     self.session_login()
