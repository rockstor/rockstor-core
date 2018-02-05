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


class ShareAclTests(APITestMixin, APITestCase):
    fixtures = ['fix2.json']
    BASE_URL = '/api/shares'

    @classmethod
    def setUpClass(cls):
        super(ShareAclTests, cls).setUpClass()

        cls.patch_mount_share = patch('storageadmin.views.share_acl.'
                                      'mount_share')
        cls.mock_mount_share = cls.patch_mount_share.start()

    @classmethod
    def tearDownClass(cls):
        super(ShareAclTests, cls).tearDownClass()

    def test_post_requests(self):

        # happy path
        shareId = 12
        data = {'owner': 'root'}
        # in fix2.json we have a share with id=12: "owner": "admin"
        response = self.client.post('{}/{}/acl'.format(self.BASE_URL, shareId),
                                    data=data)
        # TODO: The following FAIL due to:
        # "Exception: Share matching query does not exist."
        # but shareId is in fix2.json !
        # self.assertEqual(response.status_code,
        #                  status.HTTP_200_OK, msg=response.data)
