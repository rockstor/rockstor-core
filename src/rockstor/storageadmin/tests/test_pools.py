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
from storageadmin.tests.test_api import APITestMixin


class PoolTests(APITestMixin, APITestCase):
    fixtures = ['fix1.json']
    BASE_URL = '/api/pools'

    @classmethod
    def setUpClass(cls):
        super(PoolTests, cls).setUpClass()

        # post mocks
        cls.patch_mount_root = patch('storageadmin.views.pool.mount_root')
        cls.mock_mount_root = cls.patch_mount_root.start()
        cls.mock_mount_root.return_value = 'foo'

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
        cls.patch_resize_pool = patch('storageadmin.views.pool.resize_pool')
        cls.mock_resize_pool = cls.patch_resize_pool.start()
        cls.mock_resize_pool = True

        # delete mocks
        cls.patch_umount_root = patch('storageadmin.views.pool.umount_root')
        cls.mock_umount_root = cls.patch_umount_root.start()
        cls.mock_umount_root.return_value = True

        # remount mocks
        cls.patch_remount = patch('storageadmin.views.pool.remount')
        cls.mock_remount = cls.patch_remount.start()
        cls.mock_remount.return_value = True

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

    def test_invalid_requests(self):
        """
        invalid pool api operations
        1. create a pool with invalid raid level
        2. create a pool with same name as an existing share
        3. get a pool that doesn't exist
        4. edit a pool that doesn't exist
        5. delete a pool that doesn't exist
        6. edit root pool
        7. delete root pool
        """
        # create pool with invalid raid level
        data = {'disks': ('sdc', 'sdd',),
                'pname': 'singlepool2',
                'raid_level': 'derp', }
        e_msg = ("Unsupported raid level. use one of: "
                 "('single', 'raid0', 'raid1', 'raid10', 'raid5', 'raid6')")
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)

        # create a pool with same name as an existing share
        data = {'disks': ('sdc', 'sdd',),
                'pname': 'share1',
                'raid_level': 'raid0', }
        e_msg = ('A Share with this name(share1) exists. Pool and Share names '
                 'must be distinct. Choose a different name')
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)

        # edit a pool that doesn't exist
        data2 = {'disks': ('sdc', 'sdd',)}
        e_msg = ('Pool(raid0pool) does not exist.')
        response4 = self.client.put('%s/raid0pool/add' % self.BASE_URL,
                                    data=data2)
        self.assertEqual(response4.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response4.data)
        self.assertEqual(response4.data['detail'], e_msg)

        # delete a pool that doesn't exist
        response5 = self.client.delete('%s/raid0pool' % self.BASE_URL)
        self.assertEqual(response5.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response5.data)
        self.assertEqual(response5.data['detail'], e_msg)

        # attempt to add disk to root pool
        e_msg = ('Edit operations are not allowed on this '
                 'Pool(rockstor_rockstor) as it contains the operating '
                 'system.')
        response2 = self.client.put('%s/rockstor_rockstor/add' % self.BASE_URL,
                                    data=data2)
        self.assertEqual(response2.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response2.data)
        self.assertEqual(response2.data['detail'], e_msg)

        # attempt to delete root pool
        e_msg = ('Deletion of Pool(rockstor_rockstor) is not allowed as it '
                 'contains the operating system.')
        response5 = self.client.delete('%s/rockstor_rockstor' % self.BASE_URL)
        self.assertEqual(response5.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response5.data)
        self.assertEqual(response5.data['detail'], e_msg)

    def test_name_regex(self):
        """Pool name must start with a alphanumeric(a-z0-9) ' 'character and can be
        followed by any of the ' 'following characters: letter(a-z),
        digits(0-9), ' 'hyphen(-), underscore(_) or a period(.).'  1. Test a
        few valid regexes (eg: pool1, Mypool, 123, etc..)  2. Test a few
        invalid regexes (eg: -pool1, .pool etc..)  3. Empty string for pool
        name 4. max length(255 character) for pool name 5. max length + 1 for
        pool name

        """
        # valid pool names
        data = {'disks': ('sdb',),
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
        e_msg = ('Pool name must start with a alphanumeric(a-z0-9) character '
                 'and can be followed by any of the following characters: '
                 'letter(a-z), digits(0-9), hyphen(-), underscore(_) or a '
                 'period(.).')
        invalid_pool_names = ('Pool $', '-pool', '.pool', '', ' ',)

        for pname in invalid_pool_names:
            data['pname'] = pname
            response = self.client.post(self.BASE_URL, data=data)
            self.assertEqual(response.status_code,
                             status.HTTP_500_INTERNAL_SERVER_ERROR,
                             msg=response.data)
            self.assertEqual(response.data['detail'], e_msg)

        # pool name with more than 255 characters
        e_msg = ('Pool name must be less than 255 characters')

        data['pname'] = 'P' + 'o' * 254 + 'l'
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)

    def test_compression(self):
        """Compression is agnostic to name, raid and number of disks. So no need to
        test it with different types of pools. Every post & remount calls this.
        1. Create a pool with invalid compression 2. Create a pool with zlib
        compression 3. Create a pool with lzo compression 4. change compression
        from zlib to lzo 5. change compression from lzo to zlib 6. disable
        zlib, enable zlib 7. disable lzo, enable lzo

        """
        # create pool with invalid compression
        data = {'disks': ('sdc', 'sdd',),
                'pname': 'singlepool',
                'raid_level': 'single',
                'compression': 'derp'}
        e_msg = ("Unsupported compression algorithm(derp). "
                 "Use one of ('lzo', 'zlib', 'no')")
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)

        # create pool with zlib compression
        data['compression'] = 'zlib'
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response.data['compression'], 'zlib')

        # change compression from zlib to lzo
        data3 = {'compression': 'lzo'}
        response3 = self.client.put('%s/singlepool/remount' % self.BASE_URL,
                                    data=data3)
        self.assertEqual(response3.status_code, status.HTTP_200_OK,
                         msg=response3.data)
        self.assertEqual(response3.data['compression'], 'lzo')

        # create pool with none compression
        data2 = {'disks': ('sde', 'sdf',),
                 'pname': 'singlepool2',
                 'raid_level': 'single'}
        response2 = self.client.post(self.BASE_URL, data=data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK,
                         msg=response2.data)
        self.assertEqual(response2.data['compression'], 'no')

        # change compression from none to lzo
        data4 = {'compression': 'lzo'}
        response4 = self.client.put('%s/singlepool2/remount' % self.BASE_URL,
                                    data=data4)
        self.assertEqual(response4.status_code, status.HTTP_200_OK,
                         msg=response4.data)
        self.assertEqual(response4.data['compression'], 'lzo')

        # change compression from lzo to zlib
        data4 = {'compression': 'zlib'}
        response4 = self.client.put('%s/singlepool2/remount' % self.BASE_URL,
                                    data=data4)
        self.assertEqual(response4.status_code, status.HTTP_200_OK,
                         msg=response4.data)
        self.assertEqual(response4.data['compression'], 'zlib')

        # disable zlib compression
        data5 = {'compression': 'no'}
        response5 = self.client.put('%s/singlepool2/remount' % self.BASE_URL,
                                    data=data5)
        self.assertEqual(response5.status_code, status.HTTP_200_OK,
                         msg=response5.data)
        self.assertEqual(response5.data['compression'], 'no')

        # enable zlib compression
        response6 = self.client.put('%s/singlepool2/remount' % self.BASE_URL,
                                    data=data4)
        self.assertEqual(response6.status_code, status.HTTP_200_OK,
                         msg=response6.data)
        self.assertEqual(response6.data['compression'], 'zlib')

        # disable lzo compression
        response7 = self.client.put('%s/singlepool/remount' % self.BASE_URL,
                                    data=data5)
        self.assertEqual(response7.status_code, status.HTTP_200_OK,
                         msg=response7.data)
        self.assertEqual(response7.data['compression'], 'no')

        # enable lzo compression
        response8 = self.client.put('%s/singlepool/remount' % self.BASE_URL,
                                    data=data3)
        self.assertEqual(response8.status_code, status.HTTP_200_OK,
                         msg=response8.data)
        self.assertEqual(response8.data['compression'], 'lzo')

    def test_mount_options(self):
        """
        Mount options are agnostic to other parameters as in compression.
        Mount validations are called every post & remount operation
        1. test invalid options (see allowed_options in the pool.py(view))
        2. test all valid options
        3. test compress-force options
        4. test invalid compress-force
        """
        # test invalid mount options
        data = {'disks': ('sde', 'sdf',),
                'pname': 'singleton',
                'raid_level': 'single',
                'compression': 'zlib',
                'mnt_options': 'alloc_star'}
        e_msg = ("mount option(alloc_star) not allowed. Make sure there "
                 "are no whitespaces in the input. Allowed options: "
                 "['fatal_errors', '', 'thread_pool', 'max_inline', "
                 "'ssd_spread', 'clear_cache', 'inode_cache', 'nodatacow', "
                 "'noatime', 'nodatasum', 'alloc_start',"
                 " 'noacl', 'compress-force', 'space_cache', 'ssd', 'discard',"
                 " 'commit', 'autodefrag', 'metadata_ratio', 'nospace_cache']")
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)

        data['mnt_options'] = 'alloc_start'
        e_msg = ('Value for mount option(alloc_start) must be an integer')
        response2 = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response2.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response2.data)
        self.assertEqual(response2.data['detail'], e_msg)

        data['mnt_options'] = 'alloc_start=derp'
        response3 = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response3.data)
        self.assertEqual(response3.data['detail'], e_msg)

        # test all valid mount options
        data['mnt_options'] = 'fatal_errors'
        response3 = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response3.status_code, status.HTTP_200_OK,
                         msg=response3.data)
        self.assertEqual(response3.data['mnt_options'], 'fatal_errors')
        self.assertEqual(response3.data['compression'], 'zlib')

        valid_mnt_options = ('fatal_errors,thread_pool=1,max_inline=2,ssd_'
                             'spread,clear_cache,inode_cache,nodatacow,'
                             'noatime,nodatasum,alloc_start=3,noacl,space_'
                             'cache,ssd,discard,commit=4,autodefrag,'
                             'metadata_ratio=5,nospace_cache')

        data2 = {'mnt_options': valid_mnt_options}
        response3 = self.client.put('%s/singleton/remount' % self.BASE_URL,
                                    data=data2)
        self.assertEqual(response3.status_code, status.HTTP_200_OK,
                         msg=response3.data)
        self.assertEqual(response3.data['mnt_options'], valid_mnt_options)

        # test invalid compress-force
        data2 = {'mnt_options': 'compress-force=1'}
        e_msg = ("compress-force is only allowed with ('lzo', 'zlib', 'no')")
        response3 = self.client.put('%s/singleton/remount' % self.BASE_URL,
                                    data=data2)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response3.data)
        self.assertEqual(response3.data['detail'], e_msg)

        # test compress-force options
        # when pool data not included in request, _validate_compression
        # sets compression to 'no' despite pool having a compression value
        data2 = {'mnt_options': 'compress-force=no'}
        response3 = self.client.put('%s/singleton/remount' % self.BASE_URL,
                                    data=data2)
        self.assertEqual(response3.status_code, status.HTTP_200_OK,
                         msg=response3.data)
        self.assertEqual(response3.data['mnt_options'], 'compress-force=no')
        self.assertEqual(response3.data['compression'], 'no')

        data2 = {'mnt_options': 'compress-force=zlib'}
        response3 = self.client.put('%s/singleton/remount' % self.BASE_URL,
                                    data=data2)
        self.assertEqual(response3.status_code, status.HTTP_200_OK,
                         msg=response3.data)
        self.assertEqual(response3.data['mnt_options'], 'compress-force=zlib')
        self.assertEqual(response3.data['compression'], 'no')

        data2 = {'mnt_options': 'compress-force=lzo'}
        response3 = self.client.put('%s/singleton/remount' % self.BASE_URL,
                                    data=data2)
        self.assertEqual(response3.status_code, status.HTTP_200_OK,
                         msg=response3.data)
        self.assertEqual(response3.data['mnt_options'], 'compress-force=lzo')
        self.assertEqual(response3.data['compression'], 'no')

    def test_single_crud(self):
        """test pool crud ops with 'single' raid config. single can be used to create
        a pool with any number of drives but drives cannot be removed.
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
        e_msg = ("'NoneType' object is not iterable")
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)

        # create pool with 1 disk
        data['disks'] = ('sdb',)
        response2 = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response2.status_code, status.HTTP_200_OK,
                         msg=response2.data)
        self.assertEqual(response2.data['name'], 'singlepool')
        self.assertEqual(response2.data['raid'], 'single')
        self.mock_btrfs_uuid.assert_called_with('sdb')
        self.assertEqual(len(response2.data['disks']), 1)

        # create pool with 2 disks
        data = {'disks': ('sdc', 'sdd',),
                'pname': 'singlepool2',
                'raid_level': 'single', }
        response3 = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response3.status_code, status.HTTP_200_OK,
                         msg=response3.data)
        self.assertEqual(response3.data['name'], 'singlepool2')
        self.assertEqual(response3.data['raid'], 'single')
        self.mock_btrfs_uuid.assert_called_with('sdc')
        self.assertEqual(len(response3.data['disks']), 2)

        # create a pool with a duplicate name
        e_msg = ('Pool(singlepool2) already exists. Choose a different name')
        response4 = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response4.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response4.data)
        self.assertEqual(response4.data['detail'], e_msg)

        # invalid put command
        e_msg = ('command(derp) is not supported.')
        response5 = self.client.put('%s/singlepool2/derp' % self.BASE_URL,
                                    data=data)
        self.assertEqual(response5.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response5.data)
        self.assertEqual(response5.data['detail'], e_msg)

        # attempt to add disk that does not exist
        data3 = {'disks': ('derp'), }
        e_msg = ('Disk(d) does not exist')
        response5 = self.client.put('%s/singlepool2/add' %
                                    self.BASE_URL, data=data3)
        self.assertEqual(response5.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response5.data)
        self.assertEqual(response5.data['detail'], e_msg)

        # add a disk that already belongs to a pool
        data4 = {'disks': ('sdc',)}
        e_msg = ('Disk(sdc) cannot be added to this Pool(singlepool) '
                 'because it belongs to another pool(singlepool2)')
        response6 = self.client.put('%s/singlepool/add' %
                                    self.BASE_URL, data=data4)
        self.assertEqual(response6.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response6.data)
        self.assertEqual(response6.data['detail'], e_msg)

        # delete pool
        response9 = self.client.delete('%s/singlepool2' % self.BASE_URL)
        self.assertEqual(response9.status_code, status.HTTP_200_OK,
                         msg=response9.data)
        self.mock_umount_root.assert_called_with('/mnt2/singlepool2')

    def test_raid0_crud(self):
        """test pool crud ops with 'raid0' raid config. raid0 can be used to create a
        pool with atleast 2 disks & disks cannot be removed 1. attempt to
        create a pool with 1 disk 2. create a pool with 2 disks 3. get pool
        4. add disk to pool 5. attempt remove disk from pool 6. remove disks
        where it shrinks the pool by a size which is greater than free space
        7. attempt raid migration 8. delete pool

        """
        data = {'disks': ('sdb',),
                'pname': 'raid0pool',
                'raid_level': 'raid0', }

        # create pool with 1 disk
        e_msg = ('At least two disks are required for the raid level: raid0')
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)

        # create pool with 2 disks
        data['disks'] = ('sdb', 'sdc',)
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response.data['name'], 'raid0pool')
        self.assertEqual(response.data['raid'], 'raid0')
        self.mock_btrfs_uuid.assert_called_with('sdb')
        # disk length assert was failing... list is 'empty'... post function
        # was not adding disks to the pool (atleast not saving them)...
        # appears they WERE added but then dropped it on DB call
        # solution: assigned disks to the pool & saved each disk
        self.assertEqual(len(response.data['disks']), 2)

        # get pool
        response1 = self.client.get('%s/raid0pool' % self.BASE_URL)
        self.assertEqual(response1.status_code, status.HTTP_200_OK,
                         msg=response1.data)
        self.assertEqual(response.data['name'], 'raid0pool')

        # add 1 disk
        data2 = {'disks': ('sdd',)}
        response2 = self.client.put('%s/raid0pool/add' %
                                    self.BASE_URL, data=data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK,
                         msg=response2.data)
        self.assertEqual(len(response2.data['disks']), 3)

        # remove disks
        response3 = self.client.put('%s/raid0pool/remove' %
                                    self.BASE_URL, data=data2)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response3.data)
        e_msg = ('Disks cannot be removed from a pool with this raid(raid0) '
                 'configuration')
        self.assertEqual(response3.data['detail'], e_msg)

        # add 3 disks & change raid_level
        data3 = {'disks': ('sde', 'sdf', 'sdg',),
                 'raid_level': 'raid1', }
        e_msg = ('A Balance process is already running for this '
                 'pool(raid0pool). Resize is not supported during a balance '
                 'process.')
        response4 = self.client.put('%s/raid0pool/add' %
                                    self.BASE_URL, data=data3)
        self.assertEqual(response4.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response4.data)
        self.assertEqual(response4.data['detail'], e_msg)

        # delete pool
        response5 = self.client.delete('%s/raid0pool' % self.BASE_URL)
        self.assertEqual(response5.status_code, status.HTTP_200_OK,
                         msg=response5.data)
        self.mock_umount_root.assert_called_with('/mnt2/raid0pool')

    def test_raid1_crud(self):
        """test pool crud ops with 'raid1' raid config. raid1 can be used to create a
        pool with atleast 2 disks & disks can be removed 1 at a time 1. attempt
        to create a pool with 1 disk 2. create a pool with 2 disks 3. add 2
        disks to pool 4. remove 1 disks 5. remove disks where it shrinks the
        pool by a size which is greater than free space 6. remove 1 more disk
        where the total number disks will be < 2 7. delete pool

        """
        data = {'disks': ('sdb',),
                'pname': 'raid1pool',
                'raid_level': 'raid1', }

        # create pool with 1 disk
        e_msg = ('At least two disks are required for the raid level: raid1')
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)

        # create pool with 2 disks
        data['disks'] = ('sdb', 'sdc',)
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response.data['name'], 'raid1pool')
        self.assertEqual(response.data['raid'], 'raid1')
        self.mock_btrfs_uuid.assert_called_with('sdb')
        self.assertEqual(len(response.data['disks']), 2)

        # add 2 disks
        data2 = {'disks': ('sdf', 'sdg',), }
        response2 = self.client.put('%s/raid1pool/add' %
                                    self.BASE_URL, data=data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK,
                         msg=response2.data)
        self.assertEqual(len(response2.data['disks']), 4)

        # remove 1 disks
        data2 = {'disks': ('sdf',), }
        response3 = self.client.put('%s/raid1pool/remove' %
                                    self.BASE_URL, data=data2)
        self.assertEqual(response3.status_code, status.HTTP_200_OK,
                         msg=response3.data)
        self.assertEqual(len(response3.data['disks']), 3)

        # remove disks where it shrinks the pool by a size which is greater
        # than free space
        self.mock_pool_usage.return_value = (14680064, 10, 2097152)
        data3 = {'disks': ('sdg',), }
        response3 = self.client.put('%s/raid1pool/remove' %
                                    self.BASE_URL, data=data3)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response3.data)
        e_msg = ("Removing these([u'sdg']) disks may shrink the pool by "
                 "2097152KB, which is greater than available free space "
                 "2097152KB. This is not supported.")
        self.assertEqual(response3.data['detail'], e_msg)
        self.mock_pool_usage.return_value = (14680064, 10, 4194305)

        # remove 1 disk
        data3 = {'disks': ('sdg',), }
        response4 = self.client.put('%s/raid1pool/remove' %
                                    self.BASE_URL, data=data3)
        self.assertEqual(response4.status_code, status.HTTP_200_OK,
                         msg=response4.data)
        self.assertEqual(len(response4.data['disks']), 2)

        # remove 1 more disk which makes the raid with invalid number of disks
        data3 = {'disks': ('sdc',), }
        e_msg = ('Disks cannot be removed from this pool because its raid '
                 'configuration(raid1) requires a minimum of 2 disks')
        response4 = self.client.put('%s/raid1pool/remove' %
                                    self.BASE_URL, data=data3)
        self.assertEqual(response4.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response4.data)
        self.assertEqual(response4.data['detail'], e_msg)

        # delete pool
        response5 = self.client.delete('%s/raid1pool' % self.BASE_URL)
        self.assertEqual(response5.status_code, status.HTTP_200_OK,
                         msg=response5.data)
        self.mock_umount_root.assert_called_with('/mnt2/raid1pool')

    def test_raid10_crud(self):
        """test pool crud ops with 'raid10' raid config. raid10 can be used to create
        a pool with atleast 4 disks & must have an even number of disks.
        1. attempt to create a pool with 1 disk 2. attempt to create a pool
        with 5 disks 3. create a pool with 4 disks 4. add 1 disk 5. remove 2
        disks 6. remove 1 disk from pool 7. resize pool making total number of
        disks less than 4 8. delete pool

        """
        data = {'disks': ('sdb',),
                'pname': 'raid10pool',
                'raid_level': 'raid10', }

        # create pool with 1 disk
        e_msg = ('A minimum of Four drives are required for the raid '
                 'level: raid10')
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)

        # create pool with 4 disks
        data['disks'] = ('sdb', 'sdc', 'sdd', 'sde',)
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response.data['name'], 'raid10pool')
        self.assertEqual(response.data['raid'], 'raid10')
        self.mock_btrfs_uuid.assert_called_with('sdb')
        self.assertEqual(len(response.data['disks']), 4)

        # add 1 disks
        data2 = {'disks': ('sdf',), }
        response1 = self.client.put('%s/raid10pool/add' %
                                    self.BASE_URL, data=data2)
        self.assertEqual(response1.status_code, status.HTTP_200_OK,
                         msg=response1.data)
        self.assertEqual(len(response1.data['disks']), 5)

        # remove 2 disks
        data3 = {'disks': ('sde', 'sdd',), }
        e_msg = ('Disks cannot be removed from this pool because its raid '
                 'configuration(raid10) requires a minimum of 4 disks')
        response4 = self.client.put('%s/raid10pool/remove' %
                                    self.BASE_URL, data=data3)
        self.assertEqual(response4.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response4.data)
        self.assertEqual(response4.data['detail'], e_msg)

        # remove 1 disk
        data3 = {'disks': ('sdf',), }
        response4 = self.client.put('%s/raid10pool/remove' %
                                    self.BASE_URL, data=data3)
        self.assertEqual(response4.status_code, status.HTTP_200_OK,
                         msg=response4.data)
        self.assertEqual(len(response4.data['disks']), 4)

        # remove 1 more disk which makes total number of disks less than 4
        data2 = {'disks': ('sdb',), }
        response4 = self.client.put('%s/raid10pool/remove' %
                                    self.BASE_URL, data=data2)
        self.assertEqual(response4.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response4.data)
        e_msg = ('Disks cannot be removed from this pool because its raid '
                 'configuration(raid10) requires a minimum of 4 disks')
        self.assertEqual(response4.data['detail'], e_msg)

        # delete pool
        response5 = self.client.delete('%s/raid10pool' % self.BASE_URL)
        self.assertEqual(response5.status_code, status.HTTP_200_OK,
                         msg=response5.data)
        self.mock_umount_root.assert_called_with('/mnt2/raid10pool')

    def test_raid5_crud(self):
        """test pool crud ops with 'raid5' raid config. raid5 can be used to create a
        pool with at least 2 disks 1. attempt to create a pool with 1 disk
        2. create a pool with 2 disks 3. add 2 disks to pool 4. remove 2 disks
        5. remove disk that does not belong to pool 6. resize pool making total
        number of disks less than 2 7. delete pool

        """
        data = {'disks': ('sdb',),
                'pname': 'raid5pool',
                'raid_level': 'raid5', }

        # create pool with 1 disk
        e_msg = ('Two or more disks are required for the raid level: raid5')
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)

        # create pool with 2 disks
        data['disks'] = ('sdb', 'sdc',)
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response.data['name'], 'raid5pool')
        self.assertEqual(response.data['raid'], 'raid5')
        self.mock_btrfs_uuid.assert_called_with('sdb')
        self.assertEqual(len(response.data['disks']), 2)

        # add 2 disks
        data2 = {'disks': ('sdf', 'sdg',), }
        response2 = self.client.put('%s/raid5pool/add' % self.BASE_URL,
                                    data=data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK,
                         msg=response2.data)
        self.assertEqual(len(response2.data['disks']), 4)

        # remove 2 disks
        response4 = self.client.put('%s/raid5pool/remove' % self.BASE_URL,
                                    data=data2)
        self.assertEqual(response4.status_code, status.HTTP_200_OK,
                         msg=response4.data)
        self.assertEqual(len(response4.data['disks']), 2)

        # remove a disk 'sde' that does not belong to the pool
        data2 = {'disks': ('sde',), }
        response4 = self.client.put('%s/raid5pool/remove' %
                                    self.BASE_URL, data=data2)
        self.assertEqual(response4.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response4.data)
        e_msg = ('Disk(sde) cannot be removed because it does not belong '
                 'to this Pool(raid5pool)')
        self.assertEqual(response4.data['detail'], e_msg)

        # remove 1 more disk which makes total number of disks less than 2
        data2 = {'disks': ('sdb',), }
        response4 = self.client.put('%s/raid5pool/remove' %
                                    self.BASE_URL, data=data2)
        self.assertEqual(response4.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response4.data)
        e_msg = ('Disks cannot be removed from this pool because its raid '
                 'configuration(raid5) requires a minimum of 2 disks')
        self.assertEqual(response4.data['detail'], e_msg)

        # delete pool
        response5 = self.client.delete('%s/raid5pool' % self.BASE_URL)
        self.assertEqual(response5.status_code, status.HTTP_200_OK,
                         msg=response5.data)
        self.mock_umount_root.assert_called_with('/mnt2/raid5pool')

    def test_raid6_crud(self):
        """test pool crud ops with 'raid6' raid config. raid6 can be used to create a
        pool with at least 3 disks & disks cannot be removed 1. attempt to
        create a pool with 1 disk 2. create a pool with 3 disks 3. add 2 disks
        to pool 4. remove disk that does not belong to pool 5. remove 2 disks
        6. remove 1 more disk which makes total number of disks less than 3
        7. delete pool

        """
        data = {'disks': ('sdb',),
                'pname': 'raid6pool',
                'raid_level': 'raid6', }

        # create pool with 1 disk
        e_msg = ('Three or more disks are required for the raid level: raid6')
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)

        # create pool with 3 disks
        data['disks'] = ('sdb', 'sdc', 'sdd',)
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response.data['name'], 'raid6pool')
        self.assertEqual(response.data['raid'], 'raid6')
        self.mock_btrfs_uuid.assert_called_with('sdb')
        self.assertEqual(len(response.data['disks']), 3)

        # add 2 disks
        data2 = {'disks': ('sdf', 'sdg',), }
        response2 = self.client.put('%s/raid6pool/add' %
                                    self.BASE_URL, data=data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK,
                         msg=response2.data)
        self.assertEqual(len(response2.data['disks']), 5)

        # remove a disk 'sde' that does not belong to the pool
        data2 = {'disks': ('sde',), }
        response4 = self.client.put('%s/raid6pool/remove' %
                                    self.BASE_URL, data=data2)
        self.assertEqual(response4.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response4.data)
        e_msg = ('Disk(sde) cannot be removed because it does not belong to '
                 'this Pool(raid6pool)')
        self.assertEqual(response4.data['detail'], e_msg)

        # remove 2 disks
        data2 = {'disks': ('sdf', 'sdg',), }
        response4 = self.client.put('%s/raid6pool/remove' %
                                    self.BASE_URL, data=data2)
        self.assertEqual(response4.status_code, status.HTTP_200_OK,
                         msg=response4.data)
        self.assertEqual(len(response4.data['disks']), 3)

        # remove 1 more disk which makes total number of disks less than 3
        data2 = {'disks': ('sdb',), }
        response4 = self.client.put('%s/raid6pool/remove' %
                                    self.BASE_URL, data=data2)
        self.assertEqual(response4.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response4.data)
        e_msg = ('Disks cannot be removed from this pool because its raid '
                 'configuration(raid6) requires a minimum of 3 disks')
        self.assertEqual(response4.data['detail'], e_msg)

        # delete pool
        response5 = self.client.delete('%s/raid6pool' % self.BASE_URL)
        self.assertEqual(response5.status_code, status.HTTP_200_OK,
                         msg=response5.data)
        self.mock_umount_root.assert_called_with('/mnt2/raid6pool')

    def test_raid_migration(self):
        """
        test raid migrations in put add command
        1. create 'raid0' pool with 2 disks
        2. invalid migration (attempt to add < current disks & change raid)
        3. valid migration (add > current disks & change raid)
        4. create 'raid1' pool with 2 disks
        5. invalid migration ('raid1' to 'raid0')
        """
        # create 'raid0' pool with 2 disks
        data = {'disks': ('sdb', 'sdc',),
                'pname': 'raid0pool',
                'raid_level': 'raid0', }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response.data['name'], 'raid0pool')
        self.assertEqual(response.data['raid'], 'raid0')
        self.mock_btrfs_uuid.assert_called_with('sdb')
        self.assertEqual(len(response.data['disks']), 2)

        # add 1 disk & change raid_level
        data2 = {'disks': ('sdd',),
                 'raid_level': 'raid1', }
        response4 = self.client.put('%s/raid0pool/add' % self.BASE_URL,
                                    data=data2)
        self.assertEqual(response4.status_code, status.HTTP_200_OK,
                         msg=response4.data)
        self.assertEqual(len(response4.data['disks']), 3)
        self.assertEqual(response4.data['raid'], 'raid1')

        # remove 1 disk & change raid_level
        data2 = {'disks': ('sdc',),
                 'raid_level': 'raid0', }
        e_msg = ('Raid configuration cannot be changed while removing disks')
        response4 = self.client.put('%s/raid0pool/remove' % self.BASE_URL,
                                    data=data2)
        self.assertEqual(response4.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response4.data)
        self.assertEqual(response4.data['detail'], e_msg)

        # create 'raid1' pool with 2 disks
        data4 = {'disks': ('sdf', 'sdg',),
                 'pname': 'raid1pool',
                 'raid_level': 'raid1', }
        response = self.client.post(self.BASE_URL, data=data4)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response.data['name'], 'raid1pool')
        self.assertEqual(response.data['raid'], 'raid1')
        self.mock_btrfs_uuid.assert_called_with('sdf')
        self.assertEqual(len(response.data['disks']), 2)

        # migrate 'raid1' to 'single'
        data5 = {'disks': ('sdh',),
                 'raid_level': 'single', }
        e_msg = ('Pool migration from raid1 to single is not supported.')
        response4 = self.client.put('%s/raid1pool/add' % self.BASE_URL,
                                    data=data5)
        self.assertEqual(response4.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response4.data)
        self.assertEqual(response4.data['detail'], e_msg)

        # invalid migrate 'raid1' to 'raid10' with total disks < 4
        e_msg = ('A minimum of Four drives are required for the raid '
                 'level: raid10')
        data5 = {'disks': ('sdh',),
                 'raid_level': 'raid10', }
        response4 = self.client.put('%s/raid1pool/add' % self.BASE_URL,
                                    data=data5)
        self.assertEqual(response4.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response4.data)
        self.assertEqual(response4.data['detail'], e_msg)

        # invalid migrate from raid1 to raid6 with total disks < 3
        e_msg = ('A minimum of Three drives are required for the raid '
                 'level: raid6')
        data5 = {'disks': [],
                 'raid_level': 'raid6', }
        response4 = self.client.put('%s/raid1pool/add' % self.BASE_URL,
                                    data=data5)
        self.assertEqual(response4.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response4.data)
        self.assertEqual(response4.data['detail'], e_msg)

        # migrate 'raid1' to 'raid10'
        data5 = {'disks': ('sdh', 'sde'),
                 'raid_level': 'raid10', }
        response4 = self.client.put('%s/raid1pool/add' % self.BASE_URL,
                                    data=data5)
        self.assertEqual(response4.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response4.data['name'], 'raid1pool')
        self.assertEqual(response4.data['raid'], 'raid10')
        self.assertEqual(len(response4.data['disks']), 4)

    @mock.patch('storageadmin.views.share_command.Share')
    def test_delete_pool(self, mock_share):

        # delete pool that is not empty
        e_msg = ("Pool(pool1) is not empty. Delete is not allowed until all "
                 "shares in the pool are deleted")
        response5 = self.client.delete('%s/pool1' % self.BASE_URL)
        self.assertEqual(response5.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response5.data)
        self.assertEqual(response5.data['detail'], e_msg)
