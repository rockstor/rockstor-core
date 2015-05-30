__author__ = 'samrichards'

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

class ShareTests(APITestMixin, APITestCase):
    fixtures = ['fix1.json']
    BASE_URL = '/api/shares'

    @classmethod
    def setUpClass(cls):
        super(ShareTests, cls).setUpClass()

        # post mocks
        cls.patch_add_share = patch('storageadmin.views.share.add_share')
        cls.mock_add_share = cls.patch_add_share.start()
        cls.mock_add_share.return_value = True

        cls.patch_share_id = patch('storageadmin.views.share.share_id')
        cls.mock_share_id = cls.patch_share_id.start()
        cls.mock_share_id.return_value = 'derp'

        cls.patch_update_quota = patch('storageadmin.views.share.update_quota')
        cls.mock_update_quota = cls.patch_update_quota.start()
        cls.mock_update_quota.return_value = True

        cls.patch_is_share_mounted = patch('storageadmin.views.share.is_share_mounted')
        cls.mock_is_share_mounted = cls.patch_is_share_mounted.start()
        cls.mock_is_share_mounted.return_value = True

        cls.patch_set_property = patch('storageadmin.views.share.set_property')
        cls.mock_set_property = cls.patch_set_property.start()
        cls.mock_set_property.return_value = True

        # put mocks
        cls.patch_share_usage = patch('storageadmin.views.share.share_usage')
        cls.mock_share_usage = cls.patch_share_usage.start()
        cls.mock_share_usage.return_value = 500

        # delete mocks
        cls.patch_remove_share = patch('storageadmin.views.share.remove_share')
        cls.mock_remove_share = cls.patch_remove_share.start()
        cls.mock_remove_share.return_value = 'foo'

        # error handling run_command mocks
        # cls.patch_run_command = patch('storageadmin.util.run_command')
        # cls.mock_run_command = cls.patch_run_command.start()
        # cls.mock_run_command.return_value = True

    @classmethod
    def tearDownClass(cls):
        super(ShareTests, cls).tearDownClass()
        # patch.stopall()

    # def setUp(self):
        # self.client.login(username='admin', password='admin')
        # super(ShareTests, self).setUp()
        # APITestMixin.setUp()

    # def tearDown(self):
        # self.client.logout()
        # super(ShareTests, self).tearDown()
        # APITestMixin.tearDown()

    # def test_auth(self):
    #     """
    #     Test unauthorized api access
    #     """
    #     self.client.logout()
    #     response = self.client.get(self.BASE_URL)
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # def test_get(self):
    #     """
    #     Test GET request
    #     1. Get base URL
    #     2. Get nonexistant share
    #     """
    #     response = self.client.get(self.BASE_URL)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
    #
    #     # get share that doesn't exist
    #     response1 = self.client.get('%s/invalid' % self.BASE_URL)
    #     self.assertEqual(response1.status_code, status.HTTP_404_NOT_FOUND, msg=response1.data)

    def test_name_regex(self):
        """
        Share name must start with a alphanumeric(a-z0-9) ' 'character and can be
        followed by any of the ' 'following characters: letter(a-z),
        digits(0-9), ' 'hyphen(-), underscore(_) or a period(.).'
        1. Test a few valid regexes (eg: share1, Myshare, 123, etc..)
        2. Test a few invalid regexes (eg: -share1, .share etc..)
        3. Empty string for share name
        4. max length(255 character) for share name
        5. max length + 1 for share name
        """
        # valid share names
        data = {'pool': 'rockstor_rockstor', 'size': 1000}
        valid_names = ('123share', 'SHARE_TEST', 'Zzzz...', '1234', 'myshare',
                       'Sha' + 'r' * 250 + 'e',)
        for sname in valid_names:
            data['sname'] = sname
            response = self.client.post(self.BASE_URL, data=data)
            self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
            self.assertEqual(response.data['name'], sname)

        # invalid pool names
        e_msg = ('Share name must start with a alphanumeric(a-z0-9) character '
                 'and can be followed by any of the following characters: '
                 'letter(a-z), digits(0-9), hyphen(-), underscore(_) or a period(.).')
        invalid_names = ('Share $', '-share', '.share', '', ' ',
                              'Sh' + 'a' * 254 + 're',)
        for sname in invalid_names:
            data['sname'] = sname
            response = self.client.post(self.BASE_URL, data=data)
            self.assertEqual(response.status_code,
                             status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
            self.assertEqual(response.data['detail'], e_msg)

    def test_create(self):
        """
        Test POST request to create shares
        1. Create share on a nonexistent pool
        2. Create share on root pool
        3. Create share with invalid compression
        4. Create shares with invalid sizes
        5. Create shares with duplicate names
        """
        # create a share on a pool that does not exist
        data = {'sname': 'rootshare', 'pool': 'does_not_exist', 'size': 1048576}
        e_msg = ('Pool(does_not_exist) does not exist.')
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)

        # create a share on root pool
        data['pool'] = 'rockstor_rockstor'
        response2 = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response2.status_code, status.HTTP_200_OK, msg=response2.data)
        self.assertEqual(response2.data['name'], 'rootshare')

        # create a share with invalid compression
        data['compression'] = 'invalid'
        e_msg2 = ("Unsupported compression algorithm(invalid). Use one of ('lzo', 'zlib', 'no')")
        response3 = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response3.data)
        self.assertEqual(response3.data['detail'], e_msg2)

        # create a share with invalid size (too small)
        data2 = {'sname': 'too_small', 'pool': 'rockstor_rockstor', 'size': 1}
        e_msg3 = ('Share size should atleast be 100KB. Given size is 1KB')
        response4 = self.client.post(self.BASE_URL, data=data2)
        self.assertEqual(response4.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response4.data)
        self.assertEqual(response4.data['detail'], e_msg3)

        # create a share with invalid size (non integer)
        data2['size'] = 'non int'
        e_msg4 = ('Share size must be an integer')
        response5 = self.client.post(self.BASE_URL, data=data2)
        self.assertEqual(response5.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response5.data)
        self.assertEqual(response5.data['detail'], e_msg4)

        # create share with same name as a pool that already exists
        data3 = {'sname': 'rockstor_rockstor', 'pool': 'rockstor_rockstor', 'size': 1048576}
        e_msg5 = ('A Pool with this name(rockstor_rockstor) exists. Share and Pool names must be distinct. Choose a different name')
        response6 = self.client.post(self.BASE_URL, data=data3)
        self.assertEqual(response6.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response6.data)
        self.assertEqual(response6.data['detail'], e_msg5)

        # create share with name that already exists
        data3['sname'] = 'rootshare'
        e_msg6 = ('Share(rootshare) already exists. Choose a different name')
        response7 = self.client.post(self.BASE_URL, data=data3)
        self.assertEqual(response7.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response7.data)
        self.assertEqual(response7.data['detail'], e_msg6)        

        # test share with a pool that has no disks

        # test replica command

    def test_resize(self):
        """
        Test PUT request to update size of share
        1. Create valid share
        2. Valid resize
        3. Resize nonexistent share
        4. Resize share below current usage value
        5. Resize share below minimum 100KB
        """

        #create new share
        data = {'sname': 'rootshare', 'pool': 'rockstor_rockstor', 'size': 100}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data['name'], 'rootshare')

        # resize a share
        # data2 = {'sname': 'rootshare', 'pool': 'rockstor_rockstor', 'size': 1000}
        data2 = {'size': 1000}
        response2 = self.client.put('%s/rootshare' % self.BASE_URL, data=data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK, msg=response2.data)
        self.assertEqual(response2.data['size'], 1000)

        # resize a share that doesn't exist
        data3 = {'sname': 'invalid', 'size': 1500}
        response3 = self.client.put('%s/invalid' % self.BASE_URL, data=data3)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response3.data)
        e_msg = ('Share(invalid) does not exist.')
        self.assertEqual(response3.data['detail'], e_msg)

        # resize to below current share usage value
        data3 = {'size': 400}
        response3 = self.client.put('%s/rootshare' % self.BASE_URL, data=data3)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response3.data)
        e_msg = ('Unable to resize because requested new size(400KB) is less '
                 'than current usage(500KB) of the share.')
        self.assertEqual(response3.data['detail'], e_msg)

        # resize below 100KB
        self.mock_share_usage.return_value = 50
        data3 = {'size': 99}
        response3 = self.client.put('%s/rootshare' % self.BASE_URL, data=data3)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response3.data)
        e_msg = ('Share size should atleast be 100KB. Given size is 99KB')
        self.assertEqual(response3.data['detail'], e_msg)

    def test_compression(self):
        """
        Test PUT request to update share compression_algo
        1. Create a share with invalid compression
        2. Create a share with zlib compression
        3. Create a share with lzo compression
        4. change compression from zlib to lzo
        5. change compression from lzo to zlib
        6. disable zlib, enable zlib
        7. disable lzo, enable lzo
        """

        # create share with invalid compression
        data = {'sname': 'rootshare', 'pool': 'rockstor_rockstor',
                'size': 100, 'compression': 'derp'}
        e_msg = ("Unsupported compression algorithm(derp). "
                 "Use one of ('lzo', 'zlib', 'no')")
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)

        # create share with zlib compression
        data['compression'] = 'zlib'
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        # self.assertEqual(response.data, 'derp')
        self.assertEqual(response.data['compression_algo'], 'zlib')

        # create share with lzo compression
        data2 = {'sname': 'share2', 'pool': 'rockstor_rockstor',
                'size': 100, 'compression': 'lzo'}
        response2 = self.client.post(self.BASE_URL, data=data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK, msg=response2.data)
        self.assertEqual(response2.data['compression_algo'], 'lzo')

        # change compression from zlib to lzo
        data3 = {'compression': 'lzo'}
        # data3 = {'sname': 'rootshare', 'pool': 'rockstor_rockstor',
        #         'size': 100, 'compression': 'lzo'}
        # data3 = {'group': u'root', 'name': u'rootshare', 'perms': u'755', 'r_usage': -1, 'e_usage': -1, 'snapshots': [], 'compression_algo': u'lzo', 'owner': u'root', 'replica': False, 'qgroup': u'0/derp', 'toc': u'2015-05-24T06:08:50.406267Z', 'subvol_name': u'rootshare', 'size': 100, 'nfs_exports': [], u'id': 1, 'pool': OrderedDict([(u'id', 1), ('disks', [OrderedDict([(u'id', 1), ('pool_name', u'rockstor_rockstor'), ('name', u'sda3'), ('size', 8912896), ('offline', False), ('parted', False), ('btrfs_uuid', u'b71dd067-abd9-48ca-8e48-67c7c5cb17de'), ('model', None), ('serial', u'VBb419f409-272c21e5'), ('transport', None), ('vendor', None), ('smart_available', False), ('smart_enabled', False), ('pool', 1)])]), ('free', 8924160), ('reclaimable', 0), ('name', u'rockstor_rockstor'), ('uuid', u'b71dd067-abd9-48ca-8e48-67c7c5cb17de'), ('size', 8924160), ('raid', u'single'), ('toc', u'2015-04-11T00:31:29.550000Z'), ('compression', None), ('mnt_options', None)]), 'uuid': None}
        # TODO should be PUT not POST
        # response3 = self.client.post('%s/rootshare/compress' % self.BASE_URL, data=data3)
        # TODO suman -- need "compress" command? currently doesn't allow PUTs
        response3 = self.client.put('%s/rootshare' % self.BASE_URL, data=data3)
        self.assertEqual(response3.status_code, status.HTTP_200_OK, msg=response3.data)
        self.assertEqual(response3.data['compression_algo'], 'lzo')

        # change compression from lzo to zlib
        data4 = {'compression': 'zlib'}
        response4 = self.client.put('%s/share2' % self.BASE_URL, data=data4)
        self.assertEqual(response4.status_code, status.HTTP_200_OK, msg=response4.data)
        self.assertEqual(response4.data['compression_algo'], 'zlib')

        # disable zlib compression
        data5 = {'compression': 'no'}
        response5 = self.client.put('%s/share2' % self.BASE_URL, data=data5)
        self.assertEqual(response5.status_code, status.HTTP_200_OK, msg=response5.data)
        self.assertEqual(response5.data['compression_algo'], 'no')

        # enable zlib compression
        response6 = self.client.put('%s/share2' % self.BASE_URL, data=data4)
        self.assertEqual(response6.status_code, status.HTTP_200_OK, msg=response6.data)
        self.assertEqual(response6.data['compression_algo'], 'zlib')

        # disable lzo compression
        response7 = self.client.put('%s/rootshare' % self.BASE_URL, data=data5)
        self.assertEqual(response7.status_code, status.HTTP_200_OK, msg=response7.data)
        self.assertEqual(response7.data['compression_algo'], 'no')

        # enable lzo compression
        response8 = self.client.put('%s/rootshare' % self.BASE_URL, data=data3)
        self.assertEqual(response8.status_code, status.HTTP_200_OK, msg=response8.data)
        self.assertEqual(response8.data['compression_algo'], 'lzo')

    def test_delete(self):
        """
        Test DELETE request on share
        1. Create valid share
        2. Delete share
        3. Delete nonexistent share
        """

        # create share
        data = {'sname': 'rootshare', 'pool': 'rockstor_rockstor', 'size': 100}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data['name'], 'rootshare')

        # delete share
        response9 = self.client.delete('%s/rootshare' % self.BASE_URL)
        self.assertEqual(response9.status_code, status.HTTP_200_OK, msg=response9.data)
        assert self.mock_remove_share.called
        self.assertEqual(response9.data, None)

        # delete a share that doesn't exist
        e_msg = ('Share(invalid) does not exist.')
        response3 = self.client.delete('%s/invalid' % self.BASE_URL)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response3.data)
        self.assertEqual(response3.data['detail'], e_msg)

        # TODO test delete on shares w/ snapshots... requires creating snapshots (views/snapshot.py)
