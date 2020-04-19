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
from rest_framework import serializers
import mock
from mock import patch

from storageadmin import serializers
from storageadmin.models import Snapshot, Pool, Share
from storageadmin.tests.test_api import APITestMixin


class ShareAclTests(APITestMixin, APITestCase):
    fixtures = ['fix2.json']
    BASE_URL = '/api/shares'

    @classmethod
    def setUpClass(cls):
        super(ShareAclTests, cls).setUpClass()

        cls.patch_mount_share = patch('storageadmin.views.share_acl.'
                                      'mount_share')
        cls.mock_mount_share = cls.patch_mount_share.start()

        # patch chown - system.acl wrappers for run_command
        cls.patch_chown = patch('storageadmin.views.share_acl.chown')
        cls.mock_chown = cls.patch_chown.start()
        cls.mock_chown.return_value = ([''], [''], 0)

        # patch chmod - system.acl wrapper for run_command
        cls.patch_chmod = patch('storageadmin.views.share_acl.chmod')
        cls.mock_chmod = cls.patch_chmod.start()
        cls.mock_chmod.return_value = ([''], [''], 0)

    @classmethod
    def tearDownClass(cls):
        super(ShareAclTests, cls).tearDownClass()

    # # May need to moc the ShareSerializer
    # @mock.patch('storageadmin.views.share_acl.ShareSerializer')
    # # we require Snapshot mock as ShareSerializer includes a snapshots field,
    # # see: storageadmin/serializers.py
    # @mock.patch('storageadmin.serializers.Pool')
    # @mock.patch('storageadmin.serializers.Snapshot')
    # @mock.patch('storageadmin.views.share_acl.Share')
    # def test_post_requests(self, mock_share, mock_snapshot, mock_pool,
    #                        mock_share_serializer):
    #
    #     class MockShareSerializer(serializers.ModelSerializer):
    #         mount_status = serializers.CharField()
    #         is_mounted = serializers.BooleanField()
    #         pqgroup_exist = serializers.BooleanField()
    #
    #         class Meta:
    #             model = Share
    #
    #         def __init__(self, **kwargs):
    #             pass
    #
    #     # Mocking from object avoids having to also mock a pool instance
    #     # for self.pool.
    #     class MockShare(object):
    #         def __init__(self, **kwargs):
    #             self.id = 55
    #             self.name = 'share3'
    #             self.subvol_name = 'share3'
    #             self.pool = 1
    #             self.size = 8924160
    #             self.is_mounted = True
    #             self.snapshot_set = None
    #             # self.snapshots = []
    #
    #         def save(self):
    #             pass
    #
    #     class MockPool(object):
    #         def __init__(self, **kwargs):
    #             self.id = 1
    #             self.name = 'rockstor_rockstor'
    #             self.disk_set = None
    #
    #     mock_share.objects.get.side_effect = MockShare
    #     mock_snapshot.objects.get.side_effect = Snapshot.DoesNotExist
    #     mock_share_serializer.objects.get.side_effect = MockShareSerializer
    #
    #     mock_pool.objects.get.side_effect = MockPool
    #     mock_pool.objects.get.disk_set.side_effect = None
    #
    #     # happy path
    #     shareId = 12
    #     data = {'owner': 'root'}
    #     # in fix2.json we have a share with id=12: "owner": "admin"
    #     response = self.client.post('{}/{}/acl'.format(self.BASE_URL, shareId),
    #                                 data=data)
    #     # TODO: The following FAIL due to:
    #     # "Exception: Share matching query does not exist."
    #     # but shareId is in fix2.json !
    #     self.assertEqual(response.status_code,
    #                      status.HTTP_200_OK, msg=response.data)
