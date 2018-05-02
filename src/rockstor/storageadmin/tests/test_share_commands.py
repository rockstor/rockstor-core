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
from storageadmin.models import Share, Snapshot


class ShareCommandTests(APITestMixin, APITestCase):
    fixtures = ['fix1.json']
    BASE_URL = '/api/shares'

    @classmethod
    def setUpClass(cls):
        super(ShareCommandTests, cls).setUpClass()

        cls.patch_create_repclone = patch('storageadmin.views.share_command.'
                                          'create_repclone')
        cls.mock_create_repclone = cls.patch_create_repclone.start()
        cls.mock_create_repclone.return_value = Response('{"message": "ok!"}')

        cls.patch_create_clone = patch('storageadmin.views.share_command.'
                                       'create_clone')
        cls.mock_create_clone = cls.patch_create_clone.start()
        cls.mock_create_clone.return_value = Response('{"message": "ok!"}')

    @classmethod
    def tearDownClass(cls):
        super(ShareCommandTests, cls).tearDownClass()

    @mock.patch('storageadmin.views.share_command.Share')
    def test_clone_command(self, mock_share):

        """
        Test  invalid Post request
        1. Clone a share that does not exist
        2. Clone a share
        """
        # Clone a share that does not exist

        shareId = 111
        data = {'name': 'clone1'}

        # clone a share that does not exist
        mock_share.objects.get.side_effect = Share.DoesNotExist
        r = self.client.post('{}/{}/clone'.format(self.BASE_URL, shareId),
                             data=data)
        self.assertEqual(r.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=r.data)
        e_msg = 'Share id (111) does not exist.'
        self.assertEqual(r.data[0], e_msg)
        conf = {'get.side_effect': None}
        mock_share.objects.configure_mock(**conf)

        # clone happy path
        data = {'name': 'clone'}
        shareId = 2
        r = self.client.post('{}/{}/clone'.format(self.BASE_URL, shareId),
                             data=data)
        self.assertEqual(r.status_code, status.HTTP_200_OK, msg=r.data)

    @mock.patch('storageadmin.views.share_command.SambaShare')
    @mock.patch('storageadmin.views.share_command.NFSExport')
    @mock.patch('storageadmin.views.share_command.Snapshot')
    @mock.patch('storageadmin.views.share_command.Share')
    def test_rollback_command(self, mock_share, mock_snapshot, mock_nfs,
                              mock_samba):
        """
        1. Rollback share that does not exist
        2. Rollback share with no snapshot
        3. Rollback share while exported via NFS
        4. Rollback share while exported via Samba
        5. Rollback share
        """
        shareId = 2
        data = {'name': 'rsnap2'}

        # rollback share that does not exist
        mock_share.objects.get.side_effect = Share.DoesNotExist
        r = self.client.post('{}/{}/rollback'.format(self.BASE_URL, shareId),
                             data=data)
        self.assertEqual(r.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=r.data)
        e_msg = 'Share id (2) does not exist.'
        self.assertEqual(r.data[0], e_msg)

        # rollback share snapshot does not exist
        class MockShare(object):
            def __init__(self, **kwargs):
                self.id = 55
                self.name = 'rshare2'
                self.subvol_name = 'rshare2'
                self.pool = 1
                self.size = 8924160

            def save(self):
                pass

        mock_share.objects.get.side_effect = MockShare
        mock_snapshot.objects.get.side_effect = Snapshot.DoesNotExist
        r = self.client.post('{}/{}/rollback'.format(self.BASE_URL, shareId),
                             data=data)
        self.assertEqual(r.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=r.data)
        e_msg = 'Snapshot (rsnap2) does not exist for share (rshare2).'
        self.assertEqual(r.data[0], e_msg)
        mock_snapshot.objects.get.side_effect = None
        mock_share.objects.get.side_effect = None

        # rollback share while exported via NFS
        mock_share.objects.get.side_effect = MockShare
        r = self.client.post('{}/{}/rollback'.format(self.BASE_URL, shareId),
                             data=data)
        self.assertEqual(r.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=r.data)
        e_msg = ('Share (rshare2) cannot be rolled back as it is exported via '
                 'NFS. Delete NFS exports and try again.')
        self.assertEqual(r.data[0], e_msg)

        # rollback share while exported via Samba
        mock_nfs.objects.filter.return_value.exists.return_value = False
        r = self.client.post('{}/{}/rollback'.format(self.BASE_URL, shareId),
                             data=data)
        self.assertEqual(r.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=r.data)
        e_msg = ('Share (rshare2) cannot be rolled back as it is shared '
                 'via Samba. Unshare and try again.')
        self.assertEqual(r.data[0], e_msg)

        # rollback happy path
        mock_samba.objects.filter.return_value.exists.return_value = False
        r = self.client.post('{}/{}/rollback'.format(self.BASE_URL, shareId),
                             data=data)
        self.assertEqual(r.status_code, status.HTTP_200_OK, msg=r.data)
