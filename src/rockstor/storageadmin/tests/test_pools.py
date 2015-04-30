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
from mock import patch

from storageadmin.models import Pool

class PoolCRUDTests(APITestCase):
    # TODO confirm fixtures / setup / teardown runs on every method
    # TODO setup config... have a class for all mock operations? that way one setup...
    fixtures = ['fix1.json']
    BASE_URL = '/api/pools'

    def setUp(self):
        self.client.login(username='admin', password='admin')

        # post mocks
        self.patch_mount_root = patch('storageadmin.views.pool.mount_root')
        self.mock_mount_root = self.patch_mount_root.start()
        self.mock_mount_root.return_value = 'foo'

        self.patch_add_pool = patch('storageadmin.views.pool.add_pool')
        self.mock_add_pool = self.patch_add_pool.start()
        self.mock_add_pool.return_value = True

        self.patch_pool_usage = patch('storageadmin.views.pool.pool_usage')
        self.mock_pool_usage = self.patch_pool_usage.start()
        self.mock_pool_usage.return_value = (100, 10, 90)

        self.patch_btrfs_uuid = patch('storageadmin.views.pool.btrfs_uuid')
        self.mock_btrfs_uuid = self.patch_btrfs_uuid.start()
        self.mock_btrfs_uuid.return_value = 'bar'

        # put mocks (also uses pool_usage)
        self.patch_resize_pool = patch('storageadmin.views.pool.resize_pool')
        self.mock_resize_pool = self.patch_resize_pool.start()
        self.mock_resize_pool = True

        self.patch_balance_start = patch('storageadmin.views.pool.balance_start')
        self.mock_balance_start = self.patch_balance_start.start()
        self.mock_balance_start.return_value = 1

        # delete mocks
        self.patch_umount_root = patch('storageadmin.views.pool.umount_root')
        self.mock_umount_root = self.patch_umount_root.start()
        self.mock_umount_root.return_value = True

    def tearDown(self):
        patch.stopall()

    # TODO will have to execute outside of setup
    # def test_pools_auth(self):
    #     """
    #     unauthorized api access
    #     """
    #     response = self.client.get(self.BASE_URL)
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_pool_raid0_crud(self):
        """
        raid0 post, put & delete api requests
        """
        data = {'disks': ('sdb',),
                'pname': 'raid0pool',
                'raid_level': 'raid0', }

        # create pool with 1 disk
        e_msg = ('More than one disk is required for the raid level: raid0')
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)

        # create pool with 4 disks
        data['disks'] = ('sdb', 'sdc', 'sdd', 'sde',)
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data['name'], 'raid0pool')
        self.assertEqual(response.data['raid'], 'raid0')
        self.mock_btrfs_uuid.assert_called_with('sdb')
        # disk length assert was failing... list is 'empty'... post function was not adding disks to the pool (atleast not saving them)... appears they WERE added but then dropped it on DB call
        # solution: assigned disks to the pool & saved each disk
        self.assertEqual(len(response.data['disks']), 4)

        # add 2 disks
        data2 = {'disks': ('sdf', 'sdg',), }
        response2 = self.client.put('%s/raid0pool/add' % self.BASE_URL, data=data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK, msg=response2.data)
        self.assertEqual(len(response2.data['disks']), 6)

        # remove disks
        response3 = self.client.put('%s/raid0pool/remove' % self.BASE_URL, data=data2)
        self.assertEqual(response3.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response3.data)
        e_msg = ('Disks cannot be removed from a pool with this raid(raid0) configuration')
        self.assertEqual(response3.data['detail'], e_msg)

        # delete pool
        response4 = self.client.delete('%s/raid0pool' % self.BASE_URL)
        self.assertEqual(response4.status_code, status.HTTP_200_OK, msg=response4.data)
        self.mock_umount_root.assert_called_with('/mnt2/raid0pool')
        # TODO benefit to checking object is actually deleted? Or is that considered testing django ORM?
        self.assertRaises(Exception, Pool.objects.get, name='raid0pool')

#         # todo test get?
#         # response5 = self.client.get(self.BASE_URL)
#         # self.assertEqual(response5.status_code, status.HTTP_200_OK, msg=response5.data)
#         # print response5.data
#         # print dir(response5.data)
#         # self.assertEqual(len(response5.data['results'][0]['disks']), 1)

    def test_pool_raid1_crud(self):
        """
        raid1 post, put & delete api requests
        """
        data = {'disks': ('sdb',),
                'pname': 'raid1pool',
                'raid_level': 'raid1', }

        # create pool with 1 disk
        e_msg = ('At least two disks are required for the raid level: raid1')
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)

        # create pool with 4 disks
        data['disks'] = ('sdb', 'sdc', 'sdd', 'sde',)
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data['name'], 'raid1pool')
        self.assertEqual(response.data['raid'], 'raid1')
        self.mock_btrfs_uuid.assert_called_with('sdb')
        self.assertEqual(len(response.data['disks']), 4)

        # add 2 disks
        data2 = {'disks': ('sdf', 'sdg',), }
        response2 = self.client.put('%s/raid1pool/add' % self.BASE_URL, data=data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK, msg=response2.data)
        self.assertEqual(len(response2.data['disks']), 6)

        # remove 2 disks
        response3 = self.client.put('%s/raid1pool/remove' % self.BASE_URL, data=data2)
        self.assertEqual(response3.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response3.data)
        e_msg = ('Only one disk can be removed at once from this pool because of its raid configuration(raid1)')
        self.assertEqual(response3.data['detail'], e_msg)

        # remove 1 disk
        data3 = {'disks': ('sde',), }
        response4 = self.client.put('%s/raid1pool/remove' % self.BASE_URL, data=data3)
        self.assertEqual(response4.status_code, status.HTTP_200_OK, msg=response4.data)
        self.assertEqual(len(response4.data['disks']), 5)

        # delete pool
        response5 = self.client.delete('%s/raid1pool' % self.BASE_URL)
        self.assertEqual(response5.status_code, status.HTTP_200_OK, msg=response5.data)
        self.mock_umount_root.assert_called_with('/mnt2/raid1pool')


    def test_pool_raid10_crud(self):
        """
        raid10 post, put & delete api requests
        """
        data = {'disks': ('sdb',),
                'pname': 'raid10pool',
                'raid_level': 'raid10', }

        # create pool with 1 disk
        e_msg = ('A minimum of Four drives are required for the raid level: raid10')
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)
        
        # create pool with odd disks
        data['disks'] = ('sdb', 'sdc', 'sdd', 'sde', 'sdf',)
        e_msg = ('Even number of drives are required for the raid level: raid10')
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)        

        # create pool with 4 disks
        data['disks'] = ('sdb', 'sdc', 'sdd', 'sde',)
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data['name'], 'raid10pool')
        self.assertEqual(response.data['raid'], 'raid10')
        self.mock_btrfs_uuid.assert_called_with('sdb')
        self.assertEqual(len(response.data['disks']), 4)

        # add 1 disk
        data2 = {'disks': ('sdf',), }
        response1 = self.client.put('%s/raid10pool/add' % self.BASE_URL, data=data2)
        self.assertEqual(response1.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response1.data)
        e_msg = ('raid10 requires an even number of drives. Total provided = 1')
        self.assertEqual(response1.data['detail'], e_msg)

        # add 2 disks
        data2 = {'disks': ('sdf', 'sdg',), }
        response2 = self.client.put('%s/raid10pool/add' % self.BASE_URL, data=data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK, msg=response2.data)
        self.assertEqual(len(response2.data['disks']), 6)

        # remove 2 disks
        response3 = self.client.put('%s/raid10pool/remove' % self.BASE_URL, data=data2)
        self.assertEqual(response3.status_code, status.HTTP_200_OK, msg=response3.data)
        self.assertEqual(len(response3.data['disks']), 4)

        # remove 1 disk
        data3 = {'disks': ('sde',), }
        response4 = self.client.put('%s/raid10pool/remove' % self.BASE_URL, data=data3)
        self.assertEqual(response4.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response4.data)
        e_msg = ('Only two disks can be removed at once from this pool because of its raid configuration(raid10)')
        self.assertEqual(response4.data['detail'], e_msg)        

        # delete pool
        response5 = self.client.delete('%s/raid10pool' % self.BASE_URL)
        self.assertEqual(response5.status_code, status.HTTP_200_OK, msg=response5.data)
        self.mock_umount_root.assert_called_with('/mnt2/raid10pool')

    def test_pool_raid5_crud(self):
        """
        raid5 post, put & delete api requests
        """
        data = {'disks': ('sdb',),
                'pname': 'raid5pool',
                'raid_level': 'raid5', }

        # create pool with 1 disk
        e_msg = ('Three or more disks are required for the raid level: raid5')
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)

        # create pool with 4 disks
        data['disks'] = ('sdb', 'sdc', 'sdd', 'sde',)
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data['name'], 'raid5pool')
        self.assertEqual(response.data['raid'], 'raid5')
        self.mock_btrfs_uuid.assert_called_with('sdb')
        self.assertEqual(len(response.data['disks']), 4)

        # add 2 disks
        data2 = {'disks': ('sdf', 'sdg',), }
        response2 = self.client.put('%s/raid5pool/add' % self.BASE_URL, data=data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK, msg=response2.data)
        self.assertEqual(len(response2.data['disks']), 6)
        
        # remove 2 disks
        response4 = self.client.put('%s/raid5pool/remove' % self.BASE_URL, data=data2)
        self.assertEqual(response4.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response4.data)
        e_msg = ('Disk removal is not supported for pools with raid5/6 configuration')
        self.assertEqual(response4.data['detail'], e_msg)

        # delete pool
        response5 = self.client.delete('%s/raid5pool' % self.BASE_URL)
        self.assertEqual(response5.status_code, status.HTTP_200_OK, msg=response5.data)
        self.mock_umount_root.assert_called_with('/mnt2/raid5pool')
        
    def test_pool_raid6_crud(self):
        """
        raid6 post, put & delete api requests
        """
        data = {'disks': ('sdb',),
                'pname': 'raid6pool',
                'raid_level': 'raid6', }

        # create pool with 1 disk
        e_msg = ('Four or more disks are required for the raid level: raid6')
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)

        # create pool with 4 disks
        data['disks'] = ('sdb', 'sdc', 'sdd', 'sde',)
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data['name'], 'raid6pool')
        self.assertEqual(response.data['raid'], 'raid6')
        self.mock_btrfs_uuid.assert_called_with('sdb')
        self.assertEqual(len(response.data['disks']), 4)

        # add 2 disks
        data2 = {'disks': ('sdf', 'sdg',), }
        response2 = self.client.put('%s/raid6pool/add' % self.BASE_URL, data=data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK, msg=response2.data)
        self.assertEqual(len(response2.data['disks']), 6)
        
        # remove 2 disks
        response4 = self.client.put('%s/raid6pool/remove' % self.BASE_URL, data=data2)
        self.assertEqual(response4.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response4.data)
        e_msg = ('Disk removal is not supported for pools with raid5/6 configuration')
        self.assertEqual(response4.data['detail'], e_msg)

        # delete pool
        response5 = self.client.delete('%s/raid6pool' % self.BASE_URL)
        self.assertEqual(response5.status_code, status.HTTP_200_OK, msg=response5.data)
        self.mock_umount_root.assert_called_with('/mnt2/raid6pool')