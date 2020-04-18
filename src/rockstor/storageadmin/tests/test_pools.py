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
from django.conf import settings
from rest_framework import status
from rest_framework.test import APITestCase
import mock
from mock import patch
from storageadmin.models import Disk, Pool
from storageadmin.tests.test_api import APITestMixin


class PoolTests(APITestMixin, APITestCase):
    fixtures = ['test_pools.json']
    BASE_URL = '/api/pools'

    @classmethod
    def setUpClass(cls):
        super(PoolTests, cls).setUpClass()

        # post mocks
        cls.patch_mount_root = patch('storageadmin.views.pool.mount_root')
        cls.mock_mount_root = cls.patch_mount_root.start()
        cls.mock_mount_root.return_value = '/mnt2/fake-pool'

        cls.patch_add_pool = patch('storageadmin.views.pool.add_pool')
        cls.mock_add_pool = cls.patch_add_pool.start()
        cls.mock_add_pool.return_value = True

        cls.patch_pool_usage = patch('storageadmin.views.pool.pool_usage')
        cls.mock_pool_usage = cls.patch_pool_usage.start()
        cls.mock_pool_usage.return_value = (14680064, 10, 4194305)

        cls.patch_btrfs_uuid = patch('storageadmin.views.pool.btrfs_uuid')
        cls.mock_btrfs_uuid = cls.patch_btrfs_uuid.start()
        cls.mock_btrfs_uuid.return_value = 'bar'

        # put mocks (also uses pool_usage)
        cls.patch_resize_pool = patch('storageadmin.views.pool.resize_pool_cmd')
        cls.mock_resize_pool = cls.patch_resize_pool.start()
        cls.mock_resize_pool = None

        # odd how we need this as should return 0 if above resize_pool_cmd mock working.
        cls.patch_start_resize_pool = patch('storageadmin.views.pool.start_resize_pool')
        cls.mock_start_resize_pool = cls.patch_start_resize_pool.start()
        cls.mock_start_resize_pool = [''], [''], 0


        # delete mocks
        cls.patch_umount_root = patch('storageadmin.views.pool.umount_root')
        cls.mock_umount_root = cls.patch_umount_root.start()
        cls.mock_umount_root.return_value = True

        # remount mocks
        cls.patch_remount = patch('storageadmin.views.pool.remount')
        cls.mock_remount = cls.patch_remount.start()
        cls.mock_remount.return_value = True

        # mock Pool models fs/btrfs.py pool_usage() so @property 'free' works.
        cls.patch_pool_usage = patch('storageadmin.models.pool.pool_usage')
        cls.mock_pool_usage = cls.patch_pool_usage.start()
        cls.mock_pool_usage.return_value = 0

        # mock Pool mount status to always return True, this side steps many reports of:
        # "Pool member / raid edits require an active mount.  Please see the
        # "Maintenance required" section." i.e. pr #2010 on GitHub.
        cls.patch_mount_status = patch('storageadmin.models.pool.mount_status')
        cls.mock_mount_status = cls.patch_mount_status.start()
        cls.mock_mount_status.return_value = True



        # create a fake root disk instance
        cls.fake_root_disk = Disk(id=1, name='virtio-0', serial='0',
                                  size=5242880, parted=False,
                                  role={"root": "btrfs"})
        # create a collection of 6 x 5 GB virtio disk instances with serial
        # from 1-6, id = 2-7
        cls.fake_disk_1 = Disk(id=2, name='virtio-1', serial='1', size=5242880,
                               parted=False, btrfs_uuid=None)
        cls.fake_disk_2 = Disk(id=3, name='virtio-2', serial='2', size=5242880,
                               parted=False, btrfs_uuid=None)
        cls.fake_disk_3 = Disk(id=4, name='virtio-3', serial='3', size=5242880,
                               parted=False)
        cls.fake_disk_4 = Disk(id=5, name='virtio-4', serial='4', size=5242880,
                               parted=False)
        cls.fake_disk_5 = Disk(id=6, name='virtio-5', serial='5', size=5242880,
                               parted=False)
        cls.fake_disk_6 = Disk(id=7, name='virtio-6', serial='6', size=5242880,
                               parted=False)

        # mocs to allow share create, see test_delete_pool_with_share
        # TODO: remove these once we successfully mock share existence.
        ###############################################################
        cls.patch_add_share = patch('storageadmin.views.share.add_share')
        cls.mock_add_share = cls.patch_add_share.start()
        cls.mock_add_share.return_value = True

        cls.patch_update_quota = patch('storageadmin.views.share.update_quota')
        cls.mock_update_quota = cls.patch_update_quota.start()
        cls.mock_update_quota.return_value = [''], [''], 0

        cls.patch_share_pqgroup_assign = patch('storageadmin.views.share.'
                                               'share_pqgroup_assign')
        cls.mock_share_pqgroup_assign = cls.patch_share_pqgroup_assign.start()
        cls.mock_share_pqgroup_assign.return_value = True

        cls.patch_set_property = patch('storageadmin.views.share.set_property')
        cls.mock_set_property = cls.patch_set_property.start()
        cls.mock_set_property.return_value = True

        cls.patch_mount_share = patch('storageadmin.views.share.mount_share')
        cls.mock_mount_share = cls.patch_mount_share.start()
        cls.mock_mount_share.return_value = True

        cls.patch_qgroup_id = patch('storageadmin.views.share.qgroup_id')
        cls.mock_qgroup_id = cls.patch_qgroup_id.start()
        cls.mock_qgroup_id.return_value = '0f123f'

        cls.patch_qgroup_create = patch('storageadmin.views.share.'
                                        'qgroup_create')
        cls.mock_qgroup_create = cls.patch_qgroup_create.start()
        cls.mock_qgroup_create.return_value = '1'

        cls.patch_volume_usage = patch('storageadmin.views.share.volume_usage')
        cls.mock_volume_usage = cls.patch_volume_usage.start()
        # potential issue here as volume_usage returns either 2 or 4 values
        # When called with 2 parameters (pool, volume_id) it returns 2 values.
        # But with 3 parameters (pool, volume_id, pvolume_id) it returns 4
        # values if the last parameter is != None.
        cls.mock_volume_usage.return_value = (500, 500)
        # End of temp share mocks, see previous TODO:
        ###############################################################

    @classmethod
    def tearDownClass(cls):
        super(PoolTests, cls).tearDownClass()

    def test_get(self):
        """
        Test GET request
        1. Get base URL
        2. Get nonexistant pool
        """
        self.get_base(self.BASE_URL)

    @mock.patch('storageadmin.views.pool.Share')
    @mock.patch('storageadmin.views.pool.Disk')
    def test_invalid_requests_1(self, mock_disk, mock_share):
        """
        invalid pool api operations
        2. create a pool with same name as an existing share
        """

        mock_disk.objects.get.return_value = self.fake_disk_1
        mock_share.objects.filter(pool=1,
                                  name='share1').exists.return_value = True

        # create a pool with same name as an existing share
        data = {'disks': ('virtio-1', 'virtio-2',),
                'pname': 'share1',
                'raid_level': 'raid0', }
        e_msg = ('A share with this name (share1) exists. Pool and share '
                 'names must be distinct. '
                 'Choose a different name.')
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data[0], e_msg)

    @mock.patch('storageadmin.views.pool.Disk')
    def test_invalid_requests_2(self, mock_disk):
        """
        invalid pool api operations
        1. create a pool with invalid raid level

        3. get a pool that doesn't exist
        4. edit a pool that doesn't exist
        5. delete a pool that doesn't exist
        6. edit root pool
        7. delete root pool
        """

        mock_disk.objects.get.return_value = self.fake_disk_1
        # mock_disk.objects.get(id=3).return_value = self.fake_disk_2

        # create pool with invalid raid level
        data = {'disks': ('virtio-1', 'virtio-2',),
                'pname': 'singlepool2',
                'raid_level': 'derp', }
        e_msg = ("Unsupported raid level. Use one of: "
                 "('single', 'raid0', 'raid1', 'raid10', 'raid5', 'raid6').")
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data[0], e_msg)

        # edit a pool that doesn't exist
        data2 = {'disks': ('virtio-1', 'virtio-2',)}
        pId = 99999
        e_msg = 'Pool with id ({}) does not exist.'.format(pId)
        response4 = self.client.put('{}/{}/add'.format(self.BASE_URL, pId),
                                    data=data2)
        self.assertEqual(response4.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response4.data)
        self.assertEqual(response4.data[0], e_msg)

        # delete a pool that doesn't exist
        response5 = self.client.delete('{}/{}'.format(self.BASE_URL, pId))
        self.assertEqual(response5.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response5.data)
        self.assertEqual(response5.data[0], e_msg)

    @mock.patch('storageadmin.views.pool.Pool')
    @mock.patch('storageadmin.views.pool.Disk')
    def test_invalid_root_pool_edits(self, mock_disk, mock_pool):

        # mock a root pool (role='root')
        temp_pool = Pool(id=1, name='rockstor_rockstor', size=88025459,
                         role='root')
        mock_pool.objects.get.return_value = temp_pool

        # mock disk to use in attempted root pool edit (disk add)
        mock_disk.objects.get.return_value = self.fake_disk_1

        # attempt to add disk to root pool
        # TODO: remove rockstor_rockstor hard coding as can, via DNS during
        # TODO: install be any name (usually prior name of machine on network).

        data = {'disks': ('virtio-1',)}
        pId = temp_pool.id
        e_msg = ('Edit operations are not allowed on this '
                 'pool ({}) as it contains the operating '
                 'system.').format(temp_pool.name)
        response2 = self.client.put('{}/1/add'.format(self.BASE_URL, pId),
                                    data=data)
        self.assertEqual(response2.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response2.data)
        self.assertEqual(response2.data[0], e_msg)

        # attempt to delete root pool
        e_msg = ('Deletion of pool ({}) is not allowed as it '
                 'contains the operating system.').format(temp_pool.name)
        response5 = self.client.delete('{}/{}'.format(self.BASE_URL, pId))
        self.assertEqual(response5.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response5.data)
        self.assertEqual(response5.data[0], e_msg)

    @mock.patch('storageadmin.views.pool.Disk')
    def test_name_regex(self, mock_disk):
        """
        1. Test a few valid regexes
        2. Test a few invalid regexes
        3. Empty string for pool name
        4. max length(255 character) for pool name
        5. max length + 1 for pool name
        """

        mock_disk.objects.get.return_value = self.fake_disk_2

        # valid pool names
        data = {'disks': ('virtio-2',),
                'raid_level': 'single', }
        valid_names = ('123pool', 'POOL_TEST', 'Zzzz...', '1234', 'mypool',
                       'P' + 'o' * 253 + 'l',)
        for pname in valid_names:
            data['pname'] = pname
            response = self.client.post(self.BASE_URL, data=data)
            self.assertEqual(response.status_code, status.HTTP_200_OK,
                             msg=response.data)
            self.assertEqual(response.data['name'], pname)

        # invalid pool names
        # TODO: Test needs updating:
        e_msg = ('Invalid characters in pool name. Following '
                 'characters are allowed: letter(a-z or A-Z), '
                 'digit(0-9), '
                 'hyphen(-), underscore(_) or a period(.).')
        # The invalid_pool_names list is based on above description, some are
        # POSIX valid but ruled out as less portable.
        invalid_pool_names = ('Pool 1', 'Pa$sign', '/pool', ':pool', '\pool',
                              'Pquestion?mark', 'Pasteri*', '', ' ',)

        for pname in invalid_pool_names:
            data['pname'] = pname
            response = self.client.post(self.BASE_URL, data=data)
            self.assertEqual(response.status_code,
                             status.HTTP_500_INTERNAL_SERVER_ERROR,
                             msg=response.data)
            self.assertEqual(response.data[0], e_msg)

        # pool name with more than 255 characters
        e_msg = 'Pool name must be less than 255 characters.'

        data['pname'] = 'P' + 'o' * 254 + 'l'
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data[0], e_msg)

    @mock.patch('storageadmin.views.pool.Disk')
    def test_compression(self, mock_disk):
        """
        Compression is agnostic to name, raid and number of disks. So no
        need to test it with different types of pools. Every post & remount
        calls this.
        - Create a pool with invalid compression
        - Create a pool with zlib compression (singlepool)
        - change from zlib to lzo
        - Create a pool with no compression (singlepool2)
        - change from no to lzo
        - change from lzo to zlib
        - disable zlib
        - enable zlib
        - disable lzo (singlepool)
        - enable lzo
        """

        mock_disk.objects.get.return_value = self.fake_disk_1

        # create pool with invalid compression
        data = {'disks': ('virtio-1', 'virtio-2',),
                'pname': 'singlepool',
                'raid_level': 'single',
                'compression': 'derp'}
        e_msg = ("Unsupported compression algorithm (derp). "
                 "Use one of ('lzo', 'zlib', 'no').")
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data[0], e_msg)

        # create pool with zlib compression
        data['compression'] = 'zlib'
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response.data['compression'], 'zlib')

        temp_pool = Pool.objects.get(name='singlepool')
        pId = temp_pool.id

        # change compression from zlib to lzo
        comp_lzo = {'compression': 'lzo'}
        response3 = self.client.put('{}/{}/remount'.format(self.BASE_URL, pId),
                                    data=comp_lzo)
        self.assertEqual(response3.status_code, status.HTTP_200_OK,
                         msg=response3.data)
        self.assertEqual(response3.data['compression'], 'lzo')

        # Leave this pool for a bit at lzo.

        # create another pool with no compression
        data2 = {'disks': ('virtio-1', 'virtio-2',),
                 'pname': 'singlepool2',
                 'raid_level': 'single'}
        response2 = self.client.post(self.BASE_URL, data=data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK,
                         msg=response2.data)
        self.assertEqual(response2.data['compression'], 'no')

        temp_pool2 = Pool.objects.get(name='singlepool2')
        pId2 = temp_pool2.id

        # change compression from no to lzo
        response4 = self.client.put('{}/{}/remount'.format(self.BASE_URL,
                                                           pId2),
                                    data=comp_lzo)
        self.assertEqual(response4.status_code, status.HTTP_200_OK,
                         msg=response4.data)
        self.assertEqual(response4.data['compression'], 'lzo')

        # change compression from lzo to zlib
        comp_zlib = {'compression': 'zlib'}
        response4 = self.client.put('{}/{}/remount'.format(self.BASE_URL,
                                                           pId2),
                                    data=comp_zlib)
        self.assertEqual(response4.status_code, status.HTTP_200_OK,
                         msg=response4.data)
        self.assertEqual(response4.data['compression'], 'zlib')

        # disable zlib compression
        comp_no = {'compression': 'no'}
        response5 = self.client.put('{}/{}/remount'.format(self.BASE_URL,
                                                           pId2),
                                    data=comp_no)
        self.assertEqual(response5.status_code, status.HTTP_200_OK,
                         msg=response5.data)
        self.assertEqual(response5.data['compression'], 'no')

        # enable zlib compression
        response6 = self.client.put('{}/{}/remount'.format(self.BASE_URL,
                                                           pId2),
                                    data=comp_zlib)
        self.assertEqual(response6.status_code, status.HTTP_200_OK,
                         msg=response6.data)
        self.assertEqual(response6.data['compression'], 'zlib')

        # back to original pool which was at lzo

        # disable lzo compression (original pool)
        response7 = self.client.put('{}/{}/remount'.format(self.BASE_URL,
                                                           pId),
                                    data=comp_no)
        self.assertEqual(response7.status_code, status.HTTP_200_OK,
                         msg=response7.data)
        self.assertEqual(response7.data['compression'], 'no')

        # enable lzo compression (original pool)
        response8 = self.client.put('{}/{}/remount'.format(self.BASE_URL,
                                                           pId),
                                    data=comp_lzo)
        self.assertEqual(response8.status_code, status.HTTP_200_OK,
                         msg=response8.data)
        self.assertEqual(response8.data['compression'], 'lzo')

    @mock.patch('storageadmin.views.pool.Disk')
    def test_mount_options(self, mock_disk):
        """
        Mount options are agnostic to other parameters as in compression.
        Mount validations are called every post & remount operation
        1. test invalid options (see allowed_options in the pool.py(view))
        2. test all valid options
        3. test compress-force options
        4. test invalid compress-force
        """

        mock_disk.objects.get.return_value = self.fake_disk_1

        # test invalid mount options
        data = {'disks': ('virtio-1', 'virtio-2',),
                'pname': 'singleton',
                'raid_level': 'single',
                'compression': 'zlib',
                'mnt_options': 'alloc_star'}

        allowed_options = {
            'alloc_start': int,
            'autodefrag': None,
            'clear_cache': None,
            'commit': int,
            'compress-force': settings.COMPRESSION_TYPES,
            'degraded': None,
            'discard': None,
            'fatal_errors': None,
            'inode_cache': None,
            'max_inline': int,
            'metadata_ratio': int,
            'noacl': None,
            'noatime': None,
            'nodatacow': None,
            'nodatasum': None,
            'nospace_cache': None,
            'nossd': None,
            'ro': None,
            'rw': None,
            'skip_balance': None,
            'space_cache': None,
            'ssd': None,
            'ssd_spread': None,
            'thread_pool': int,
            '': None,
        }

        e_msg = ('mount option ({}) not allowed. Make sure there are '
                 'no whitespaces in the input. Allowed options: '
                 '({}).').format(data['mnt_options'],
                                 sorted(allowed_options.keys()))

        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data[0], e_msg)

        data['mnt_options'] = 'alloc_start'
        e_msg = 'Value for mount option (alloc_start) must be an integer.'
        response2 = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response2.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response2.data)
        self.assertEqual(response2.data[0], e_msg)

        data['mnt_options'] = 'alloc_start=derp'
        response3 = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response3.data)
        self.assertEqual(response3.data[0], e_msg)

        # test all valid mount options
        data['mnt_options'] = 'fatal_errors'
        response3 = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response3.status_code, status.HTTP_200_OK,
                         msg=response3.data)
        self.assertEqual(response3.data['mnt_options'], 'fatal_errors')
        self.assertEqual(response3.data['compression'], 'zlib')

        valid_mnt_options = ('alloc_start=3,autodefrag,clear_cache,commit=4,'
                             'degraded,discard,fatal_errors,inode_cache,'
                             'max_inline=2,metadata_ratio=5,noacl,noatime,'
                             'nodatacow,nodatasum,nospace_cache,nossd,ro,'
                             'rw,skip_balance,space_cache,ssd,ssd_spread,'
                             'thread_pool=1')

        # hacky as depends on above success in creating this pool.
        temp_pool = Pool.objects.get(name='singleton')
        pId = temp_pool.id

        data2 = {'mnt_options': valid_mnt_options}
        response3 = self.client.put('{}/{}/remount'.format(self.BASE_URL, pId),
                                    data=data2)
        self.assertEqual(response3.status_code, status.HTTP_200_OK,
                         msg=response3.data)
        self.assertEqual(response3.data['mnt_options'], valid_mnt_options)

        # test invalid compress-force
        data2 = {'mnt_options': 'compress-force=1'}
        e_msg = "compress-force is only allowed with ('lzo', 'zlib', 'no')."
        response3 = self.client.put('{}/{}/remount'.format(self.BASE_URL, pId),
                                    data=data2)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response3.data)
        self.assertEqual(response3.data[0], e_msg)

        # test compress-force options
        # when pool data not included in request, _validate_compression
        # sets compression to 'no' despite pool having a compression value
        data2 = {'mnt_options': 'compress-force=no'}
        response3 = self.client.put('{}/{}/remount'.format(self.BASE_URL, pId),
                                    data=data2)
        self.assertEqual(response3.status_code, status.HTTP_200_OK,
                         msg=response3.data)
        self.assertEqual(response3.data['mnt_options'], 'compress-force=no')
        self.assertEqual(response3.data['compression'], 'no')

        data2 = {'mnt_options': 'compress-force=zlib'}
        response3 = self.client.put('{}/{}/remount'.format(self.BASE_URL, pId),
                                    data=data2)
        self.assertEqual(response3.status_code, status.HTTP_200_OK,
                         msg=response3.data)
        self.assertEqual(response3.data['mnt_options'], 'compress-force=zlib')
        self.assertEqual(response3.data['compression'], 'no')

        data2 = {'mnt_options': 'compress-force=lzo'}
        response3 = self.client.put('{}/{}/remount'.format(self.BASE_URL, pId),
                                    data=data2)
        self.assertEqual(response3.status_code, status.HTTP_200_OK,
                         msg=response3.data)
        self.assertEqual(response3.data['mnt_options'], 'compress-force=lzo')
        self.assertEqual(response3.data['compression'], 'no')

    @mock.patch('storageadmin.views.pool.Disk')
    def test_single_crud(self, mock_disk):
        """
        test pool crud ops with 'single' raid config. single can be used to
        create a pool with any number of drives but drives cannot be removed.
        1. create a pool with 0 disks 2. create a pool with 1 disk 3. create a
        pool with 2 disks 4. create a pool with a duplicate name 5. add 0 disks
        6. add 2 disks to pool 7. invalid put command 8. add a disk that
        doesn't exist 9. add a disk that already belongs to a pool 10. remove
        disk that doesn't belong to pool 11. remove 2 disks from pool
        12. delete pool

        """

        # create pool with 0 disks
        data = {'pname': 'singlepool',
                'raid_level': 'single', }
        e_msg = "'NoneType' object is not iterable"
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data[0], e_msg)

        mock_disk.objects.get.return_value = self.fake_disk_2

        # create pool with 1 disk
        data['disks'] = ('virtio-2',)
        response2 = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response2.status_code, status.HTTP_200_OK,
                         msg=response2.data)
        self.assertEqual(response2.data['name'], 'singlepool')
        self.assertEqual(response2.data['raid'], 'single')
        self.mock_btrfs_uuid.assert_called_with('virtio-2')
        self.assertEqual(len(response2.data['disks']), 1)

        mock_disk.objects.get.return_value = self.fake_disk_3

        # create pool with 2 disks
        data = {'disks': ('virtio-3', 'virtio-4',),
                'pname': 'singlepool2',
                'raid_level': 'single', }
        response3 = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response3.status_code, status.HTTP_200_OK,
                         msg=response3.data)
        self.assertEqual(response3.data['name'], 'singlepool2')
        self.assertEqual(response3.data['raid'], 'single')
        self.mock_btrfs_uuid.assert_called_with('virtio-3')
        # TODO: The following fails with 1 != 2
        # self.assertEqual(len(response3.data['disks']), 2)

        # create a pool with a duplicate name
        e_msg = 'Pool (singlepool2) already exists. Choose a different name.'
        # N.B. works by using the exact same data as in prior test above.
        response4 = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response4.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response4.data)
        self.assertEqual(response4.data[0], e_msg)

        # hacky as depends on above success in creating this pool.
        temp_pool = Pool.objects.get(name='singlepool2')
        pId = temp_pool.id

        # invalid put command
        e_msg = 'Command (derp) is not supported.'
        response5 = self.client.put('{}/{}/derp'.format(self.BASE_URL, pId),
                                    data=data)
        self.assertEqual(response5.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response5.data)
        self.assertEqual(response5.data[0], e_msg)

        # mock_disk.objects.get.return_value = Disk.DoesNotExist

        # attempt to add disk that does not exist
        # TODO: Fails with:
        # 'Problem with role filter of disks.' !=
        # 'Disk with id (d) does not exist.'
        # Need to explicitly indicate Disk.DoesNotExist as looks like the role
        # filter catches this instead.
        # data3 = {'disks': ('derp'), }
        # e_msg = 'Disk with id (d) does not exist.'
        # response5 = self.client.put('{}/{}/add'.format(self.BASE_URL, pId),
        #                             data=data3)
        # self.assertEqual(response5.status_code,
        #                  status.HTTP_500_INTERNAL_SERVER_ERROR,
        #                  msg=response5.data)
        # self.assertEqual(response5.data[0], e_msg)

        mock_disk.objects.get.return_value = self.fake_disk_2

        # add a disk that already belongs to a pool
        data4 = {'disks': ('virtio-2',)}
        e_msg = ('Disk (virtio-2) cannot be added to this pool (singlepool2) '
                 'because it belongs to another pool (singlepool).')
        response6 = self.client.put('{}/{}/add'.format(self.BASE_URL, pId),
                                    data=data4)
        self.assertEqual(response6.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response6.data)
        self.assertEqual(response6.data[0], e_msg)

        # delete pool
        response9 = self.client.delete('{}/{}'.format(self.BASE_URL, pId))
        self.assertEqual(response9.status_code, status.HTTP_200_OK,
                         msg=response9.data)
        self.mock_umount_root.assert_called_with('/mnt2/singlepool2')

    @mock.patch('storageadmin.views.pool.Disk')
    def test_raid0_crud(self, mock_disk):
        """
        test pool crud ops with 'raid0' raid config. Raid0 can be used to
        create a pool with atleast 2 disks & disks cannot be removed:
        1. Attempt to create a pool with 1 disk
        2. create a pool with 2 disks
        3. get pool
        4. add disk to pool
        5. attempt remove disk from pool
        6. remove disks where it shrinks the pool by a size which is greater
        than free space.
        7. attempt raid migration
        8. delete pool

        """

        mock_disk.objects.get.return_value = self.fake_disk_2

        data = {'disks': ('virtio-2',),
                'pname': 'raid0pool',
                'raid_level': 'raid0', }

        # create pool with 1 disk
        e_msg = 'At least 2 disks are required for the raid level: raid0.'
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data[0], e_msg)

        # create pool with 2 disks
        data['disks'] = ('virtio-1', 'virtio-2',)
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response.data['name'], 'raid0pool')
        self.assertEqual(response.data['raid'], 'raid0')
        self.mock_btrfs_uuid.assert_called_with('virtio-2')
        # disk length assert was failing... list is 'empty'... post function
        # was not adding disks to the pool (atleast not saving them)...
        # appears they WERE added but then dropped it on DB call
        # solution: assigned disks to the pool & saved each disk

        # TODO: Fails on 1 != 2 (ie only 1 disk showing)
        # self.assertEqual(len(response.data['disks']), 2)

        temp_pool = Pool.objects.get(name='raid0pool')
        pId = temp_pool.id

        # get pool
        response1 = self.client.get('{}/{}'.format(self.BASE_URL, pId))
        self.assertEqual(response1.status_code, status.HTTP_200_OK,
                         msg=response1.data)
        self.assertEqual(response.data['name'], 'raid0pool')

        mock_disk.objects.get.return_value = self.fake_disk_4

        # add 1 disk
        data2 = {'disks': ('virtio-4',)}
        response2 = self.client.put('{}/{}/add'.format(self.BASE_URL, pId),
                                    data=data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK,
                         msg=response2.data)
        self.assertEqual(response2.status_code, status.HTTP_200_OK,
                         msg=response2.data)
        # TODO: Fails on 2 != 3 (ie only 2 disks showing)
        # self.assertEqual(len(response2.data['disks']), 3)

        # remove disks
        response3 = self.client.put('{}/{}/remove'.format(self.BASE_URL, pId),
                                    data=data2)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response3.data)
        e_msg = ('Disks cannot be removed from a pool with this raid (raid0) '
                 'configuration.')
        self.assertEqual(response3.data[0], e_msg)

        # TODO: This seems hacky as doens't account for virtio-6 and virtio-7
        # responses but seems to work.
        mock_disk.objects.get.return_value = self.fake_disk_5

        # add 3 disks & change raid_level
        data3 = {'disks': ('virtio-5', 'virtio-6', 'virtio-7',),
                 'raid_level': 'raid1', }
        e_msg = ('A Balance process is already running or paused '
                 'for this pool (raid0pool). Resize is not supported '
                 'during a balance process.')
        response4 = self.client.put('{}/{}/add'.format(self.BASE_URL, pId),
                                    data=data3)
        self.assertEqual(response4.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response4.data)
        self.assertEqual(response4.data[0], e_msg)

        # delete pool
        response5 = self.client.delete('{}/{}'.format(self.BASE_URL, pId))
        self.assertEqual(response5.status_code, status.HTTP_200_OK,
                         msg=response5.data)
        self.mock_umount_root.assert_called_with('/mnt2/raid0pool')

    @mock.patch('storageadmin.views.pool.Disk')
    def test_raid1_crud(self, mock_disk):
        """
        test pool crud ops with 'raid1' raid config. raid1 can be used to
        create a pool with at least 2 disks & disks can be removed 1 at a time
        1. attempt to create a pool with 1 disk
        2. create a pool with 2 disks
        3. add 2 disks to pool
        4. remove 1 disks
        5. remove disks where it shrinks the pool by a size which is greater
        than free space
        6. remove 1 more disk where the total number disks will be < 2
        7. delete pool

        """

        mock_disk.objects.get.return_value = self.fake_disk_2

        data = {'disks': ('virtio-2',),
                'pname': 'raid1pool',
                'raid_level': 'raid1', }

        # create pool with 1 disk
        e_msg = 'At least 2 disks are required for the raid level: raid1.'
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data[0], e_msg)

        # TODO: We our mocking arrangement only allows for a single disk
        # so we end up with 1 != 2

        # create pool with 2 disks
        data['disks'] = ('virtio-2', 'virtio-3',)
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response.data['name'], 'raid1pool')
        self.assertEqual(response.data['raid'], 'raid1')
        self.mock_btrfs_uuid.assert_called_with('virtio-2')
        # TODO: The following fails with 1 != 2
        # self.assertEqual(len(response.data['disks']), 2)

        temp_pool = Pool.objects.get(name='raid1pool')
        pId = temp_pool.id

        mock_disk.objects.get.return_value = self.fake_disk_5

        # add 2 disks
        data2 = {'disks': ('virtio-5', 'virtio-6',), }
        response2 = self.client.put('{}/{}/add'.format(self.BASE_URL, pId),
                                    data=data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK,
                         msg=response2.data)
        # TODO: The following fails with 2 != 4
        # self.assertEqual(len(response2.data['disks']), 4)

        # remove 1 disks
        # TODO: Fails as it depends on the last test which also fails.
        # data2 = {'disks': ('virtio-5',), }
        # response3 = self.client.put('{}/{}/remove'.format(self.BASE_URL,
        #                                                   pId),
        #                             data=data2)
        # self.assertEqual(response3.status_code, status.HTTP_200_OK,
        #                  msg=response3.data)
        # self.assertEqual(len(response3.data['disks']), 3)

        # remove disks where it shrinks the pool by a size which is greater
        # than free space
        # TODO: Our mocking only emulates a single disk so we get:
        #  "Disks cannot be removed from this pool because its raid configuration
        #  (raid1) requires a minimum of 2 disks.' instead.
        # self.mock_pool_usage.return_value = (14680064, 10, 2097152)
        # data3 = {'disks': ('virtio-4',), }
        # response3 = self.client.put('{}/{}/remove'.format(self.BASE_URL, pId),
        #                             data=data3)
        # self.assertEqual(response3.status_code,
        #                  status.HTTP_500_INTERNAL_SERVER_ERROR,
        #                  msg=response3.data)
        # e_msg = ("Removing disks ([u'virtio-4']) may shrink the pool by "
        #          '2097152 KB, which is greater than available free '
        #          'space 2097152 KB. This is '
        #          'not supported.')
        # self.assertEqual(response3.data[0], e_msg)
        # self.mock_pool_usage.return_value = (14680064, 10, 4194305)

        # # remove 1 disk
        # data3 = {'disks': ('virtio-4',), }
        # response4 = self.client.put('{}/{}/remove'.format(self.BASE_URL, pId),
        #                             data=data3)
        # self.assertEqual(response4.status_code, status.HTTP_200_OK,
        #                  msg=response4.data)
        # self.assertEqual(len(response4.data['disks']), 2)
        #
        # # remove 1 more disk which makes the raid with invalid number of disks
        # data3 = {'disks': ('virtio-3',), }
        # e_msg = ('Disks cannot be removed from this pool because its raid '
        #          'configuration (raid1) requires a minimum of 2 disks.')
        # response4 = self.client.put('{}/{}/remove'.format(self.BASE_URL, pId),
        #                             data=data3)
        # self.assertEqual(response4.status_code,
        #                  status.HTTP_500_INTERNAL_SERVER_ERROR,
        #                  msg=response4.data)
        # self.assertEqual(response4.data[0], e_msg)

        # delete pool
        response5 = self.client.delete('{}/{}'.format(self.BASE_URL, pId))
        self.assertEqual(response5.status_code, status.HTTP_200_OK,
                         msg=response5.data)
        self.mock_umount_root.assert_called_with('/mnt2/raid1pool')

    @mock.patch('storageadmin.views.pool.Disk')
    def test_raid10_crud(self, mock_disk):
        """
        test pool crud ops with 'raid10' raid config. Raid10 can be used to
        create a pool with at least 4 disks.
        1. attempt to create a pool with 1 disk
        2. attempt to create a pool with 5 disks
        3. create a pool with 4 disks
        4. add 1 disk
        5. remove 2 disks
        6. remove 1 disk from pool
        7. resize pool making total number of disks less than 4
        8. delete pool
        """

        mock_disk.objects.get.return_value = self.fake_disk_2

        data = {'disks': ('virtio-2',),
                'pname': 'raid10pool',
                'raid_level': 'raid10', }

        # create pool with 1 disk
        e_msg = ('A minimum of 4 drives are required for the raid '
                 'level: raid10.')
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data[0], e_msg)

        # create pool with 4 disks
        data['disks'] = ('virtio-2', 'virtio-3', 'virtio-4', 'virtio-5',)
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response.data['name'], 'raid10pool')
        self.assertEqual(response.data['raid'], 'raid10')
        self.mock_btrfs_uuid.assert_called_with('virtio-2')
        # TODO: The following fails with 1 != 4
        # self.assertEqual(len(response.data['disks']), 4)

        mock_disk.objects.get.return_value = self.fake_disk_6

        temp_pool = Pool.objects.get(name='raid10pool')
        pId = temp_pool.id

        # TODO: The following fails with:
        # 'A minimum of 4 drives are required for the raid level: raid10.' !!!
        # add 1 disks
        # data2 = {'disks': ('virtio-6',), }
        # response1 = self.client.put('{}/{}/add'.format(self.BASE_URL, pId),
        #                             data=data2)
        # self.assertEqual(response1.status_code, status.HTTP_200_OK,
        #                  msg=response1.data)
        # self.assertEqual(len(response1.data['disks']), 5)

        mock_disk.objects.get.return_value = self.fake_disk_5

        # TODO: The following fails with
        # 'Disk (virtio-5) cannot be removed because it does not belong to
        # this pool (raid10pool).'
        # remove 2 disks
        # data3 = {'disks': ('virtio-5', 'virtio-4',), }
        # e_msg = ('Disks cannot be removed from this pool because its raid '
        #          'configuration (raid10) requires a minimum of 4 disks.')
        # response4 = self.client.put('{}/{}/remove'.format(self.BASE_URL,
        #                                                   pId),
        #                             data=data3)
        # self.assertEqual(response4.status_code,
        #                  status.HTTP_500_INTERNAL_SERVER_ERROR,
        #                  msg=response4.data)
        # self.assertEqual(response4.data[0], e_msg)

        mock_disk.objects.get.return_value = self.fake_disk_6

        # TODO: The following fails with
        # 'Disk (virtio-6) cannot be removed because it does not belong to
        #  this pool (raid10pool).'
        # remove 1 disk
        # data3 = {'disks': ('virtio-6',), }
        # response4 = self.client.put('{}/{}/remove'.format(self.BASE_URL,
        #                                                   pId),
        #                             data=data3)
        # self.assertEqual(response4.status_code, status.HTTP_200_OK,
        #                  msg=response4.data)
        # self.assertEqual(len(response4.data['disks']), 4)

        mock_disk.objects.get.return_value = self.fake_disk_2

        # remove 1 more disk which makes total number of disks less than 4
        data2 = {'disks': ('virtio-2',), }
        response4 = self.client.put('{}/{}/remove'.format(self.BASE_URL, pId),
                                    data=data2)
        self.assertEqual(response4.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response4.data)
        e_msg = ('Disks cannot be removed from this pool because its raid '
                 'configuration (raid10) requires a minimum of 4 disks.')
        self.assertEqual(response4.data[0], e_msg)

        # delete pool
        response5 = self.client.delete('{}/{}'.format(self.BASE_URL, pId))
        self.assertEqual(response5.status_code, status.HTTP_200_OK,
                         msg=response5.data)
        self.mock_umount_root.assert_called_with('/mnt2/raid10pool')

    @mock.patch('storageadmin.views.pool.Disk')
    def test_raid5_crud(self, mock_disk):
        """
        test pool crud ops with 'raid5' raid config. raid5 can be used to
        create a pool with at least 2 disks
        1. attempt to create a pool with 1 disk
        2. create a pool with 2 disks
        3. add 2 disks to pool
        4. remove 2 disks
        5. remove disk that does not belong to pool
        6. resize pool making total number of disks less than 2
        7. delete pool

        """

        mock_disk.objects.get.return_value = self.fake_disk_2

        data = {'disks': ('virtio-2',),
                'pname': 'raid5pool',
                'raid_level': 'raid5', }

        # create pool with 1 disk
        e_msg = '2 or more disks are required for the raid level: raid5.'
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data[0], e_msg)

        # create pool with 2 disks
        data['disks'] = ('virtio-2', 'virtio-3',)
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response.data['name'], 'raid5pool')
        self.assertEqual(response.data['raid'], 'raid5')
        self.mock_btrfs_uuid.assert_called_with('virtio-2')
        # TODO: The following fails with 1 != 2
        # self.assertEqual(len(response.data['disks']), 2)

        temp_pool = Pool.objects.get(name='raid5pool')
        pId = temp_pool.id

        mock_disk.objects.get.return_value = self.fake_disk_4

        # add 2 disks
        # data2 = {'disks': ('virtio-4', 'virtio-5',), }
        # response2 = self.client.put('{}/{}/add'.format(self.BASE_URL, pId),
        #                             data=data2)
        # self.assertEqual(response2.status_code, status.HTTP_200_OK,
        #                  msg=response2.data)
        # # TODO: The following fails with 2 != 4
        # # self.assertEqual(len(response2.data['disks']), 4)

        # remove the same 2 disks
        # response4 = self.client.put('{}/{}/remove'.format(self.BASE_URL,
        #                                                   pId),
        #                             data=data2)
        # self.assertEqual(response4.status_code, status.HTTP_200_OK,
        #                  msg=response4.data)
        # # TODO: The following fails with x != y
        # # self.assertEqual(len(response4.data['disks']), 2)

        mock_disk.objects.get.return_value = self.fake_disk_6

        # remove a disk 'virtio-6' that does not belong to the pool
        data2 = {'disks': ('virtio-6',), }
        response4 = self.client.put('{}/{}/remove'.format(self.BASE_URL, pId),
                                    data=data2)
        self.assertEqual(response4.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response4.data)
        e_msg = ('Disk (virtio-6) cannot be removed because it does not '
                 'belong to this pool (raid5pool).')
        self.assertEqual(response4.data[0], e_msg)

        mock_disk.objects.get.return_value = self.fake_disk_2

        # remove 1 more disk which makes total number of disks less than 2
        data2 = {'disks': ('virtio-2',), }
        response4 = self.client.put('{}/{}/remove'.format(self.BASE_URL, pId),
                                    data=data2)
        self.assertEqual(response4.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response4.data)
        e_msg = ('Disks cannot be removed from this pool because its raid '
                 'configuration (raid5) requires a minimum of 2 disks.')
        self.assertEqual(response4.data[0], e_msg)

        # delete pool
        response5 = self.client.delete('{}/{}'.format(self.BASE_URL, pId))
        self.assertEqual(response5.status_code, status.HTTP_200_OK,
                         msg=response5.data)
        self.mock_umount_root.assert_called_with('/mnt2/raid5pool')

    @mock.patch('storageadmin.views.pool.Disk')
    def test_raid6_crud(self, mock_disk):
        """
        test pool crud ops with 'raid6' raid config. raid6 can be used to
        create a pool with at least 3 disks & disks cannot be removed
        1. attempt to create a pool with 1 disk
        2. create a pool with 3 disks
        3. add 2 disks to pool
        4. remove disk that does not belong to pool
        5. remove 2 disks
        6. remove 1 more disk which makes total number of disks less than 3
        7. delete pool

        """

        mock_disk.objects.get.return_value = self.fake_disk_1

        data = {'disks': ('virtio-1',),
                'pname': 'raid6pool',
                'raid_level': 'raid6', }

        # create pool with 1 disk
        e_msg = '3 or more disks are required for the raid level: raid6.'
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data[0], e_msg)

        # create pool with 3 disks
        data['disks'] = ('virtio-1', 'virtio-2', 'virtio-3',)
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response.data['name'], 'raid6pool')
        self.assertEqual(response.data['raid'], 'raid6')
        self.mock_btrfs_uuid.assert_called_with('virtio-1')
        # TODO: The following fails with x != y
        # self.assertEqual(len(response.data['disks']), 3)

        # instantiate pool object so we can get it's id
        temp_pool = Pool.objects.get(name='raid6pool')
        pId = temp_pool.id

        self.fake_disk_4.pool = None
        mock_disk.objects.get.return_value = self.fake_disk_4

        # add 2 disks
        data2 = {'disks': ('virtio-4', 'virtio-5',), }
        response2 = self.client.put('{}/{}/add'.format(self.BASE_URL, pId),
                                    data=data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK,
                         msg=response2.data)
        # TODO: The following fails with 2 != 5
        # self.assertEqual(len(response2.data['disks']), 5)

        mock_disk.objects.get.return_value = self.fake_disk_6

        # remove a disk that does not belong to the pool
        data3 = {'disks': ('virtio-6',), }
        response3 = self.client.put('{}/{}/remove'.format(self.BASE_URL, pId),
                                    data=data3)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response3.data)
        e_msg = ('Disk (virtio-6) cannot be removed because it does not belong '
                 'to this pool (raid6pool).')
        self.assertEqual(response3.data[0], e_msg)

        # TODO: our prior mock_disk.objects.get.return_value = self.fake_disk_6
        #  is still in play and seems to break the following.
        #  Plus pool numbers are not working via current mock system so remarking out
        #  the following 2 tests.

        # # remove 2 disks
        # data4 = {'disks': ('virtio-4', 'virtio-5',), }
        # response4 = self.client.put('{}/{}/remove'.format(self.BASE_URL, pId),
        #                             data=data4)
        # self.assertEqual(response4.status_code, status.HTTP_200_OK,
        #                  msg=response4.data)
        # self.assertEqual(len(response4.data['disks']), 3)
        #
        # mock_disk.objects.get.return_value = self.fake_disk_3
        #
        # # remove 1 more disk which makes total number of disks less than 3
        # data2 = {'disks': ('virtio-3',), }
        # response4 = self.client.put('{}/{}/remove'.format(self.BASE_URL, pId),
        #                             data=data2)
        # self.assertEqual(response4.status_code,
        #                  status.HTTP_500_INTERNAL_SERVER_ERROR,
        #                  msg=response4.data)
        # e_msg = ('Disks cannot be removed from this pool because its raid '
        #          'configuration (raid6) requires a minimum of 3 disks.')
        # self.assertEqual(response4.data[0], e_msg)

        # delete pool
        response5 = self.client.delete('{}/{}'.format(self.BASE_URL, pId))
        self.assertEqual(response5.status_code, status.HTTP_200_OK,
                         msg=response5.data)
        self.mock_umount_root.assert_called_with('/mnt2/raid6pool')

    # @mock.patch('storageadmin.views.pool.Disk')
    # def test_raid_migration(self, mock_disk):
    #     """
    #     test raid migrations in put add command
    #     1. create 'raid0' pool with 2 disks
    #     2. invalid migration (attempt to add < current disks & change raid)
    #     3. valid migration (add > current disks & change raid)
    #     4. create 'raid1' pool with 2 disks
    #     5. invalid migration ('raid1' to 'raid0')
    #     """
    #
    #     mock_disk.objects.get.return_value = self.fake_disk_1
    #
    #     # create 'raid0' pool with 2 disks
    #     data = {'disks': ('virtio-1', 'virtio-2',),
    #             'pname': 'raid0pool',
    #             'raid_level': 'raid0', }
    #     response = self.client.post(self.BASE_URL, data=data)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK,
    #                      msg=response.data)
    #     self.assertEqual(response.data['name'], 'raid0pool')
    #     self.assertEqual(response.data['raid'], 'raid0')
    #     self.mock_btrfs_uuid.assert_called_with('virtio-1')
    #     # TODO: The following fails with 1 != 2
    #     # self.assertEqual(len(response.data['disks']), 2)
    #
    #     # instantiate pool object so we can get it's id
    #     temp_pool = Pool.objects.get(name='raid0pool')
    #     pId = temp_pool.id
    #     mock_disk.objects.get.return_value = self.fake_disk_3
    #
    #     # add 1 disk & change raid_level
    #     data2 = {'disks': ('virtio-3',),
    #              'raid_level': 'raid1', }
    #     response4 = self.client.put('{}/{}/add'.format(self.BASE_URL, pId),
    #                                 data=data2)
    #     self.assertEqual(response4.status_code, status.HTTP_200_OK,
    #                      msg=response4.data)
    #     # TODO: Fails on 2 != 3
    #     self.assertEqual(len(response4.data['disks']), 3)
    #     self.assertEqual(response4.data['raid'], 'raid1')
    #
    #     # remove 1 disk & change raid_level
    #     data2 = {'disks': ('virtio-3',),
    #              'raid_level': 'raid0', }
    #     e_msg = 'Raid configuration cannot be changed while removing disks.'
    #     response4 = self.client.put('{}/{}/remove'.format(self.BASE_URL, pId),
    #                                 data=data2)
    #     self.assertEqual(response4.status_code,
    #                      status.HTTP_500_INTERNAL_SERVER_ERROR,
    #                      msg=response4.data)
    #     self.assertEqual(response4.data[0], e_msg)
    #
    #     mock_disk.objects.get.return_value = self.fake_disk_4
    #
    #     # create 'raid1' pool with 2 disks
    #     data4 = {'disks': ('virtio-4', 'virtio-5',),
    #              'pname': 'raid1pool',
    #              'raid_level': 'raid1', }
    #     response = self.client.post(self.BASE_URL, data=data4)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK,
    #                      msg=response.data)
    #     self.assertEqual(response.data['name'], 'raid1pool')
    #     self.assertEqual(response.data['raid'], 'raid1')
    #     self.mock_btrfs_uuid.assert_called_with('virtio-4')
    #     self.assertEqual(len(response.data['disks']), 2)
    #
    #     # instantiate pool object so we can get it's id
    #     temp_pool = Pool.objects.get(name='raid1pool')
    #     pId2 = temp_pool.id
    #
    #     mock_disk.objects.get.return_value = self.fake_disk_3
    #
    #     # invalid migrate 'raid1' to 'raid10' with total disks < 4
    #     e_msg = ('A minimum of 4 drives are required for the raid '
    #              'level: raid10.')
    #     data5 = {'disks': ('virtio-3',),
    #              'raid_level': 'raid10', }
    #     response4 = self.client.put('{}/{}/add'.format(self.BASE_URL, pId2),
    #                                 data=data5)
    #     self.assertEqual(response4.status_code,
    #                      status.HTTP_500_INTERNAL_SERVER_ERROR,
    #                      msg=response4.data)
    #     self.assertEqual(response4.data[0], e_msg)
    #
    #     # invalid migrate from raid1 to raid6 with total disks < 3
    #     e_msg = ('A minimum of 3 drives are required for the raid '
    #              'level: raid6.')
    #     data5 = {'disks': [],
    #              'raid_level': 'raid6', }
    #     response4 = self.client.put('{}/{}/add'.format(self.BASE_URL, pId2),
    #                                 data=data5)
    #     self.assertEqual(response4.status_code,
    #                      status.HTTP_500_INTERNAL_SERVER_ERROR,
    #                      msg=response4.data)
    #     self.assertEqual(response4.data[0], e_msg)
    #
    #     # migrate 'raid1' to 'raid10' and specify 2 more disks
    #     data5 = {'disks': ('virtio-3', 'virtio-6'),
    #              'raid_level': 'raid10', }
    #     response4 = self.client.put('{}/{}/add'.format(self.BASE_URL, pId2),
    #                                 data=data5)
    #     self.assertEqual(response4.status_code, status.HTTP_200_OK,
    #                      msg=response.data)
    #     self.assertEqual(response4.data['name'], 'raid1pool')
    #     self.assertEqual(response4.data['raid'], 'raid10')
    #     self.assertEqual(len(response4.data['disks']), 4)

    @mock.patch('storageadmin.views.share.Pool')
    def test_delete_pool_with_share(self, mock_pool):

        # mock a pool
        temp_pool = Pool(id=2, name='mock-pool', size=88025459)
        mock_pool.objects.get.return_value = temp_pool

        # hack to avoid 'A pool with this name (share1) exists. Share and
        # pool names must be distinct. Choose a different name.
        mock_pool.objects.filter.return_value.exists.return_value = False

        # TODO: The following failed for the purposes of this test.
        # suspect we need to additional fixture info as no shares in this one.
        # # mock a share on this pool
        # temp_share = Share(id=3, name='share1', pool=temp_pool, size=4025459)
        # mock_share.objects.get.return_value = temp_share
        # mock_share.objects.filter(pool=temp_pool).exists.return_value = True

        # create new share via api on mocked pool
        # taken from test_shares.py
        data = {'sname': 'share1', 'pool': 'mock-pool', 'size': 1000}
        response = self.client.post('/api/shares', data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response.data['name'], 'share1')
        self.assertEqual(response.data['size'], 1000)

        # now to our intended test:
        # delete pool that has a share
        pId = 2
        e_msg = ("Pool ({}) is not empty. Delete is not allowed until all "
                 "shares in the pool are deleted.").format(temp_pool.name)
        response5 = self.client.delete('{}/{}'.format(self.BASE_URL, pId))
        self.assertEqual(response5.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response5.data)
        self.assertEqual(response5.data[0], e_msg)
