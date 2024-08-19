"""
Copyright (joint work) 2024 The Rockstor Project <https://rockstor.com>
Rockstor is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.
Rockstor is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
from rest_framework import status
from unittest.mock import patch

from storageadmin.models import Share, SFTP
from storageadmin.tests.test_api import APITestMixin

"""
Fixture creation instructions:

System needs 1 virtio data disk (min 5 GB). System pool not required in fixture.

- Virtio disk serial '1' - we do not required storageadmin.disk in fixture.

- Create  pool 'rock-pool' using btrfs-raid 'single' with virtio disk serial '1'.
- Create share 'share_root_owned' ('rock-pool') owner.group 'root.root': no SFTP export.
- Create share 'share_user_owned' ('rock-pool') owner.group 'admin.admin': no SFTP export.
- Create share 'share_sftp' ('rock-pool') owner.group 'admin.admin' - SFTP exported.

cd /opt/rockstor/src/rockstor
export DJANGO_SETTINGS_MODULE=settings
poetry run django-admin dumpdata storageadmin.pool storageadmin.share \
storageadmin.SFTP storageadmin.user storageadmin.group \
--natural-foreign --indent 4 > \
./storageadmin/fixtures/test_sftp.json

(strip out root pool and home share from test_sftp.json as not used)


Running this test:

cd /opt/rockstor/src/rockstor
export DJANGO_SETTINGS_MODULE=settings
poetry run django-admin test -p test_sftp.py -v 2
"""


class SFTPTests(APITestMixin):

    fixtures = ["test_api.json", "test_sftp.json"]
    BASE_URL = "/api/sftp"

    @classmethod
    def setUpClass(cls):
        super(SFTPTests, cls).setUpClass()

        # post mocks

        cls.patch_is_share_mounted = patch("storageadmin.views.sftp.is_share_mounted")
        cls.mock_is_share_mounted = cls.patch_is_share_mounted.start()
        cls.mock_is_share_mounted.return_value = True

        cls.patch_helper_mount_share = patch(
            "storageadmin.views.sftp.helper_mount_share"
        )
        cls.mock_helper_mount_share = cls.patch_helper_mount_share.start()
        cls.mock_helper_mount_share.return_value = True

        cls.patch_sftp_mount = patch("storageadmin.views.sftp.sftp_mount")
        cls.mock_sftp_mount = cls.patch_sftp_mount.start()
        cls.mock_sftp_mount.return_value = True

        # Avoid low-level chmod/rsync/sftp_user filesystem/sshd prep by mocking.
        cls.patch_rsync_for_sftp = patch("storageadmin.views.sftp.rsync_for_sftp")
        cls.mock_rsync_for_sftp = cls.patch_rsync_for_sftp.start()
        cls.mock_rsync_for_sftp.return_value = True

        cls.patch_update_sftp_user_share_config = patch(
            "storageadmin.views.sftp.update_sftp_user_share_config"
        )
        cls.mock_update_sftp_user_share_config = (
            cls.patch_update_sftp_user_share_config.start()
        )
        cls.mock_update_sftp_user_share_config.return_value = True

    @classmethod
    def tearDownClass(cls):
        super(SFTPTests, cls).tearDownClass()

    def test_get(self):
        """
        Test GET request
        1. Get base URL
        2. Get request with id
        """
        # get base URL
        self.get_base(self.BASE_URL)

        # get sftp with id
        response = self.client.get("{}/1".format(self.BASE_URL))
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response)

    def test_post_requests_1(self):
        """
        invalid sftp operations
        1. Create sftp without providing share names
        """

        # create sftp with no share names
        data = {
            "read_only": "true",
        }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = "Must provide share names."
        self.assertEqual(response.data[0], e_msg)

    # TODO: FAIL repair needed.
    def test_post_requests_2(self):
        """
        . Create sftp for root-owned share - should fail as not supported.
        . Create sftp for the share that is already sftp exported
        . Create sftp for user-owned share
        """

        # Create sftp for root-owned share - should fail as not supported.
        data = {"shares": ("share_root_owned",)}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = (
            "Share (share_root_owned) is owned by root. It cannot be "
            "exported via SFTP with root ownership."
        )
        self.assertEqual(response.data[0], e_msg)

        # Create sftp for the share that is already sftp exported
        data = {"shares": ("share_sftp",)}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = "Share (share_sftp) is already exported via SFTP."
        self.assertEqual(response.data[0], e_msg)

        # Create sftp for user-owned share - happy path
        data = {
            "shares": ("share_user_owned",),
            "read_only": "true",
        }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

    def test_delete_requests_1(self):
        """
        1. Delete sftp export that does not exist
        """

        # Delete sftp that does not exists
        sftp_id = 99999
        response = self.client.delete("{}/{}".format(self.BASE_URL, sftp_id))
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = "SFTP config for the id ({}) does not exist.".format(sftp_id)
        self.assertEqual(response.data[0], e_msg)

    def test_delete_requests_2(self):
        """
        1. Delete sftp export
        """

        # happy path
        # our fixture's existing sftp export
        sftp_share = Share.objects.get(name="share_sftp")
        sftp_export = SFTP.objects.get(share=sftp_share.id)
        sftp_id = sftp_export.id

        response = self.client.delete("{}/{}".format(self.BASE_URL, sftp_id))
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
