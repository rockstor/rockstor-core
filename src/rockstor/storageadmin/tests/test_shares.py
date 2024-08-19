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
from storageadmin.tests.test_api import APITestMixin
from storageadmin.models import Pool, Share

"""
Fixture creation instructions:

- Create root-share on ROOT system pool
- Create rock-ons-root on default ROOT system pool.
- Configure the Rock-ons service to use the rock-ons-root share. Service Disabled.

- Create rock-pool.

- Create rock-share on rock-pool.
- Create share-with-snap on rock-pool.
- Create NFS-share on rock-pool.
- Create SAMBA-share on rock-pool.
- Create SFTP-share on rock-pool (Access control admin/users).

- Create default-snapshot on share-with-snap

- Create NFS export on NFS-share - * (clients) + defaults.
- Create SAMBA export on SAMBA-share - defaults.
- Create SFTP export on SFTP-share - defaults.

- Create replication-snapshot from rock-share (snap_type="replication").

bin/django dumpdata storageadmin.pool storageadmin.share storageadmin.snapshot \
storageadmin.nfsexport storageadmin.nfsexportgroup \
storageadmin.sambashare \
storageadmin.sftp \
--natural-foreign --indent 4 > \
src/rockstor/storageadmin/fixtures/test_shares.json

# service dump from smart_manager db.
bin/django dumpdata --database smart_manager smart_manager.service \
--natural-foreign --indent 4 > \
src/rockstor/storageadmin/fixtures/test_shares-services.json

To run the tests:
cd /opt/rockstor/src/rockstor
poetry run django-admin test -v 2 -p test_shares.py
"""


class ShareTests(APITestMixin):
    databases = "__all__"
    fixtures = ["test_api.json", "test_shares.json", "test_shares-services.json"]
    BASE_URL = "/api/shares"

    @classmethod
    def setUpClass(cls):
        super(ShareTests, cls).setUpClass()

        # post mocks
        cls.patch_add_share = patch("storageadmin.views.share.add_share")
        cls.mock_add_share = cls.patch_add_share.start()
        cls.mock_add_share.return_value = True

        cls.patch_update_quota = patch("storageadmin.views.share.update_quota")
        cls.mock_update_quota = cls.patch_update_quota.start()
        cls.mock_update_quota.return_value = [""], [""], 0

        cls.patch_share_pqgroup_assign = patch(
            "storageadmin.views.share." "share_pqgroup_assign"
        )
        cls.mock_share_pqgroup_assign = cls.patch_share_pqgroup_assign.start()
        cls.mock_share_pqgroup_assign.return_value = True

        cls.patch_set_property = patch("storageadmin.views.share.set_property")
        cls.mock_set_property = cls.patch_set_property.start()
        cls.mock_set_property.return_value = True

        # Mock Share dynamic model property of Share.is_mounted.
        # At time of submission this patch is not required as below mount_share patch
        # is called if we are False.
        # Establishing to enable future tests for unmounted volumes.
        cls.patch_is_mounted = patch("storageadmin.models.share.mount_status")
        cls.mock_is_mounted = cls.patch_is_mounted.start()
        cls.mock_is_mounted.return_value = True

        cls.patch_mount_share = patch("storageadmin.views.share.mount_share")
        cls.mock_mount_share = cls.patch_mount_share.start()
        cls.mock_mount_share.return_value = True

        cls.patch_qgroup_id = patch("storageadmin.views.share.qgroup_id")
        cls.mock_qgroup_id = cls.patch_qgroup_id.start()
        cls.mock_qgroup_id.return_value = "0f123f"

        cls.patch_qgroup_create = patch("storageadmin.views.share." "qgroup_create")
        cls.mock_qgroup_create = cls.patch_qgroup_create.start()
        cls.mock_qgroup_create.return_value = "1"

        cls.patch_volume_usage = patch("storageadmin.views.share.volume_usage")
        cls.mock_volume_usage = cls.patch_volume_usage.start()
        # potential issue here as volume_usage returns either 2 or 4 values
        # When called with 2 parameters (pool, volume_id) it returns 2 values.
        # But with 3 parameters (pool, volume_id, pvolume_id) it returns 4
        # values if the last parameter is != None.
        cls.mock_volume_usage.return_value = (500, 500)

        # delete mocks
        cls.patch_remove_share = patch("storageadmin.views.share.remove_share")
        cls.mock_remove_share = cls.patch_remove_share.start()
        cls.mock_remove_share.return_value = True

        # mock Pool models fs/btrfs.py pool_usage() so @property 'free' works.
        cls.patch_pool_usage = patch("storageadmin.models.pool.pool_usage")
        cls.mock_pool_usage = cls.patch_pool_usage.start()
        cls.mock_pool_usage.return_value = 0

    @classmethod
    def tearDownClass(cls):
        super(ShareTests, cls).tearDownClass()

    def test_get(self):
        """
        Test GET request
        - Get base URL
        - Get existing share
        - Get non-existing share
        - Get w/ sort parameters
        """
        self.get_base(self.BASE_URL)

        share = Share.objects.get(name="root-share")  # no associated exports/services
        sId = share.id

        # get existing share
        response = self.client.get("{}/{}".format(self.BASE_URL, sId))
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response)

        # get non-existing share
        sId = 99999
        response = self.client.get("{}/{}".format(self.BASE_URL, sId))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, msg=response)

        # Get w/ sort parameters
        response1 = self.client.get("%s?sortby=usage&reverse=yes" % self.BASE_URL)
        self.assertEqual(response1.status_code, status.HTTP_200_OK, msg=response1.data)

        response2 = self.client.get("%s?sortby=usage" % self.BASE_URL)
        self.assertEqual(response1.status_code, status.HTTP_200_OK, msg=response2.data)

    def test_name_regex(self):
        """
        Share name must start with a alphanumeric (a-z0-9) ' 'character and
        can be followed by any of the ' 'following characters: letter(a-z),
        digits(0-9), ' 'hyphen(-), underscore(_) or a period(.).'  1. Test a
        few valid regexes (eg: share1, Myshare, 123, etc..)  2. Test a few
        invalid regexes (eg: -share1, .share etc..)  3. Empty string for share
        name 4. max length(254 characters) for share name 5. max length + 1 for
        share name
        """

        # valid share names
        data = {"pool": "ROOT", "size": 1000}
        valid_names = (
            "123share",
            "SHARE_TEST",
            "Zzzz...",
            "1234",
            "myshare",
            "Sha" + "r" * 250 + "e",
        )

        for sname in valid_names:
            data["sname"] = sname
            response = self.client.post(self.BASE_URL, data=data)
            self.assertEqual(
                response.status_code, status.HTTP_200_OK, msg=response.data
            )
            self.assertEqual(response.data["name"], sname)

        # invalid share names
        e_msg = (
            "Invalid characters in share name. Following are "
            "allowed: letter(a-z or A-Z), digit(0-9), "
            "hyphen(-), underscore(_) or a period(.)."
        )

        # The invalid_names list is based on above description, some are
        # POSIX valid but ruled out as less portable.
        invalid_names = (
            "Share 1",
            "a$sign" "/share",
            ":share",
            "\share",
            "question?mark",
            "asterix*",
            "",
            " ",
        )
        for sname in invalid_names:
            data["sname"] = sname
            response = self.client.post(self.BASE_URL, data=data)
            self.assertEqual(
                response.status_code,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                msg=response.data,
            )
            self.assertEqual(response.data[0], e_msg)

        # Share name with more than 255 characters
        e_msg = "Share name length cannot exceed 254 characters."

        data["sname"] = "Sh" + "a" * 251 + "re"
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

    def test_create(self):
        """
        Test POST request to create shares
        - Create share on non-existent pool
        - Create share with invalid compression
        - Create share with invalid size (too small)
        - Create share with invalid size (non integer)
        - Create share with existing pool name
        - Create share with existing share name
        - Create share with valid replica
        - Create share with invalid replica
        - Create share with share size > pool size
        - Create share with system reserved name
        """

        # create a share on non-existent pool
        data = {"sname": "test-share", "pool": "does_not_exist", "size": 1048576}
        e_msg = "Pool (does_not_exist) does not exist."
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

        # create a share with invalid compression
        data["pool"] = "ROOT"  # in fixure
        data["compression"] = "invalid"
        e_msg2 = (
            "Unsupported compression algorithm (invalid). Use one of "
            "('zlib', 'lzo', 'zstd', 'no')."
        )
        response3 = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response3.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response3.data,
        )
        self.assertEqual(response3.data[0], e_msg2)

        # create a share with invalid size (too small)
        data2 = {"sname": "too_small", "pool": "ROOT", "size": 1}
        e_msg3 = "Share size should be at least 100 KB. Given size is 1 KB."
        response4 = self.client.post(self.BASE_URL, data=data2)
        self.assertEqual(
            response4.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response4.data,
        )
        self.assertEqual(response4.data[0], e_msg3)

        # create a share with invalid size (non integer)
        data2["size"] = "non int"
        e_msg4 = "Share size must be an integer."
        response5 = self.client.post(self.BASE_URL, data=data2)
        self.assertEqual(
            response5.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response5.data,
        )
        self.assertEqual(response5.data[0], e_msg4)

        # create share with same name as a pool that already exists
        data3 = {"sname": "ROOT", "pool": "ROOT", "size": 1048576}
        e_msg5 = (
            "A pool with this name (ROOT) exists. Share "
            "and pool names must be distinct. Choose "
            "a different name."
        )
        response6 = self.client.post(self.BASE_URL, data=data3)
        self.assertEqual(
            response6.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response6.data,
        )
        self.assertEqual(response6.data[0], e_msg5)

        # create share with name that already exists
        data3["sname"] = "root-share"  # in fixture
        e_msg6 = "Share ({}) already exists. Choose a different name.".format(
            data3["sname"]
        )
        response7 = self.client.post(self.BASE_URL, data=data3)
        self.assertEqual(
            response7.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response7.data,
        )
        self.assertEqual(response7.data[0], e_msg6)

        # create share with valid replica
        data4 = {"sname": "valid_replica", "pool": "ROOT", "size": 100, "replica": True}
        response8 = self.client.post(self.BASE_URL, data=data4)
        self.assertEqual(response8.status_code, status.HTTP_200_OK, msg=response8.data)
        self.assertEqual(response8.data["name"], "valid_replica")
        self.assertEqual(response8.data["replica"], True)

        # create share with invalid replica
        data5 = {
            "sname": "invalid_replica",
            "pool": "ROOT",
            "size": 100,
            "replica": "non-bool",
        }
        # Py3.6 defaults to class 'str' in our test data.
        e_msg7 = "Replica must be a boolean, not (<class 'str'>)."
        response9 = self.client.post(self.BASE_URL, data=data5)
        self.assertEqual(
            response9.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response9.data,
        )
        self.assertEqual(response9.data[0], e_msg7)

        # create share with size > pool size
        data6 = {"sname": "too_big", "pool": "ROOT", "size": 10000000000000}
        response10 = self.client.post(self.BASE_URL, data=data6)
        self.assertEqual(
            response10.status_code, status.HTTP_200_OK, msg=response10.data
        )
        self.assertEqual(response10.data["name"], "too_big")
        pool = Pool.objects.get(name=data6["pool"])
        self.assertEqual(response10.data["size"], pool.size)

        # Create share with system reserved name
        data7 = {"sname": "var", "pool": "rock-pool", "size": 1048576}
        e_msg8 = f"Share name ({data7['sname']}) reserved for system. Choose a different name."
        response11 = self.client.post(self.BASE_URL, data=data7)
        self.assertEqual(
            response11.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response11.data,
        )
        self.assertEqual(response11.data[0], e_msg8)

    def test_resize(self):
        """
        Test PUT request to update size of share
        - Valid resize of user share on system pool.
        - Resize user share below share usage.
        - Resize user share below 100 KB.
        - Resize default home share.
        - Resize non-existent share.
        """

        # resize user share on system pool
        share = Share.objects.get(name="root-share")  # no associated exports/services
        sId = share.id

        new_size = {"size": 2000}
        response3 = self.client.put("{}/{}".format(self.BASE_URL, sId), data=new_size)
        self.assertEqual(response3.status_code, status.HTTP_200_OK, msg=response3.data)
        self.assertEqual(response3.data["size"], 2000)

        # resize user share on system pool to below current share usage value
        new_size = {"size": 400}
        response3 = self.client.put("{}/{}".format(self.BASE_URL, sId), data=new_size)
        self.assertEqual(
            response3.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response3.data,
        )
        e_msg = (
            "Unable to resize because requested new size 400 KB is less "
            "than current usage 500 KB of the share."
        )
        self.assertEqual(response3.data[0], e_msg)

        # resize user share on system pool to below 100KB
        self.mock_volume_usage.return_value = (50, 50)  # to avoid below usage trigger
        new_size = {"size": 99}
        response3 = self.client.put("{}/{}".format(self.BASE_URL, sId), data=new_size)
        self.assertEqual(
            response3.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response3.data,
        )
        e_msg = "Share size should be at least 100 KB. Given size is 99 KB."
        self.assertEqual(response3.data[0], e_msg)

        self.mock_volume_usage.return_value = (500, 500)

        # resize default 'home' share
        # N.B. home is only default surfaced share maintained for v3 compatibility.
        home_share = Share.objects.get(name="home")  # system default Web-UI surfaced
        home_sId = home_share.id

        new_size = {"size": 1500}
        response3 = self.client.put(
            "{}/{}".format(self.BASE_URL, home_sId), data=new_size
        )
        self.assertEqual(
            response3.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response3.data,
        )
        e_msg = (
            "Operation not permitted on this share ({}) because it is "
            "a special system share.".format(home_share.name)
        )
        self.assertEqual(response3.data[0], e_msg)

        # resize non-existent share
        sId_invalid = 99999
        new_size = {"sname": "invalid", "size": 1500}
        response3 = self.client.put(
            "{}/{}".format(self.BASE_URL, sId_invalid), data=new_size
        )
        self.assertEqual(
            response3.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response3.data,
        )
        e_msg = "Share id ({}) does not exist.".format(sId_invalid)
        self.assertEqual(response3.data[0], e_msg)

    def test_compression(self):
        """
        Test PUT request to update share compression_algo
        - Create a share with invalid compression
        - Create a share with zlib compression
        - change compression from zlib to lzo
        - Create a share with lzo compression
        - change compression from lzo to zlib
        - disable zlib
        - enable zlib
        - disable lzo
        - enable lzo
        - change compression from lzo to zstd
        """

        # create share with invalid compression
        compression_test_share = {
            "sname": "compression-test-share",
            "pool": "ROOT",
            "size": 100,
            "compression": "derp",
        }
        e_msg = (
            "Unsupported compression algorithm (derp). "
            "Use one of ('zlib', 'lzo', 'zstd', 'no')."
        )
        response = self.client.post(self.BASE_URL, data=compression_test_share)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

        # create share with zlib compression
        compression_test_share["compression"] = "zlib"  # valid compression value
        response = self.client.post(self.BASE_URL, data=compression_test_share)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["compression_algo"], "zlib")
        share = Share.objects.get(name="compression-test-share")
        sId = share.id

        # change compression from zlib to lzo
        compression_lzo = {"compression": "lzo"}
        response3 = self.client.put(
            "{}/{}".format(self.BASE_URL, sId), data=compression_lzo
        )
        self.assertEqual(response3.status_code, status.HTTP_200_OK, msg=response3.data)
        self.assertEqual(response3.data["compression_algo"], "lzo")

        # create share with lzo compression
        share_lzo_compression = {
            "sname": "compression-test-share2",
            "pool": "ROOT",
            "size": 100,
            "compression": "lzo",
        }
        response2 = self.client.post(self.BASE_URL, data=share_lzo_compression)
        self.assertEqual(response2.status_code, status.HTTP_200_OK, msg=response2.data)
        self.assertEqual(response2.data["compression_algo"], "lzo")

        # change compression from lzo to zlib
        compression_zlib = {"compression": "zlib"}
        response4 = self.client.put(
            "{}/{}".format(self.BASE_URL, sId), data=compression_zlib
        )
        self.assertEqual(response4.status_code, status.HTTP_200_OK, msg=response4.data)
        self.assertEqual(response4.data["compression_algo"], "zlib")

        # disable zlib compression
        compression_disable = {"compression": "no"}
        response5 = self.client.put(
            "{}/{}".format(self.BASE_URL, sId), data=compression_disable
        )
        self.assertEqual(response5.status_code, status.HTTP_200_OK, msg=response5.data)
        self.assertEqual(response5.data["compression_algo"], "no")

        # enable zlib compression
        response6 = self.client.put(
            "{}/{}".format(self.BASE_URL, sId), data=compression_zlib
        )
        self.assertEqual(response6.status_code, status.HTTP_200_OK, msg=response6.data)
        self.assertEqual(response6.data["compression_algo"], "zlib")

        # disable lzo compression
        response7 = self.client.put(
            "{}/{}".format(self.BASE_URL, sId), data=compression_disable
        )
        self.assertEqual(response7.status_code, status.HTTP_200_OK, msg=response7.data)
        self.assertEqual(response7.data["compression_algo"], "no")

        # enable lzo compression
        response8 = self.client.put(
            "{}/{}".format(self.BASE_URL, sId), data=compression_lzo
        )
        self.assertEqual(response8.status_code, status.HTTP_200_OK, msg=response8.data)
        self.assertEqual(response8.data["compression_algo"], "lzo")

        # change compression from lzo to zstd
        compression_zstd = {"compression": "zstd"}
        response9 = self.client.put(
            "{}/{}".format(self.BASE_URL, sId), data=compression_zstd
        )
        self.assertEqual(response9.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response9.data["compression_algo"], "zstd")

    def test_delete_exported_replicated(self):
        """
        Test DELETE request on share
        - Delete share with replication related snapshots
        - Delete share with NFS export
        - Delete share with SAMBA export
        - Delete share with SFTP export
        - Delete none-existent share
        """

        # Delete share with replication related snapshots
        share = Share.objects.get(name="rock-share")  # has replication snapshot
        sId = share.id

        # TODO: check not false positive (see: test_delete_share_with_snapshot)
        e_msg = (
            "Share ({}) cannot be deleted as it has replication "
            "related snapshots.".format(share.name)
        )
        response2 = self.client.delete("{}/{}".format(self.BASE_URL, sId))
        self.assertEqual(
            response2.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response2.data,
        )

        # Delete share with NFS export
        share = Share.objects.get(name="NFS-share")  # has replication snapshot
        sId = share.id

        e_msg = (
            "Share (NFS-share) cannot be deleted as it is exported via "
            "NFS. Delete NFS exports and try again."
        )
        response3 = self.client.delete("{}/{}".format(self.BASE_URL, sId))
        self.assertEqual(
            response3.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response3.data,
        )
        self.assertEqual(response3.data[0], e_msg)

        # Delete share with SAMBA export
        share = Share.objects.get(name="SAMBA-share")  # has replication snapshot
        sId = share.id

        e_msg = (
            "Share (SAMBA-share) cannot be deleted as it is shared via "
            "Samba. Unshare and try again."
        )
        response4 = self.client.delete("{}/{}".format(self.BASE_URL, sId))
        self.assertEqual(
            response4.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response4.data,
        )
        self.assertEqual(response4.data[0], e_msg)

        # Delete share with SFTP export
        share = Share.objects.get(name="SFTP-share")  # has replication snapshot
        sId = share.id

        e_msg = (
            "Share (SFTP-share) cannot be deleted as it is exported via "
            "SFTP. Delete SFTP export and try again."
        )
        response6 = self.client.delete("{}/{}".format(self.BASE_URL, sId))
        self.assertEqual(
            response6.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response6.data,
        )
        self.assertEqual(response6.data[0], e_msg)

        # delete none-existent share
        sId_fake = 99999
        e_msg = "Share id ({}) does not exist.".format(sId_fake)
        response9 = self.client.delete("{}/{}".format(self.BASE_URL, sId_fake))
        self.assertEqual(
            response9.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response9.data,
        )
        self.assertEqual(response9.data[0], e_msg)

    def test_delete_with_regular_snapshot(self):
        # Delete share with regular snapshot and nothing else.

        share = Share.objects.get(name="share-with-snap")  # share - regular snap only
        sId = share.id

        # TODO this test get triggered by check for snap_type='replication'

        e_msg = (
            "Share ({}) cannot be deleted as it has snapshots. "
            "Delete snapshots and try again.".format(share.name)
        )
        response5 = self.client.delete("{}/{}".format(self.BASE_URL, sId))
        self.assertEqual(
            response5.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response5.data,
        )
        self.assertEqual(response5.data[0], e_msg)

    def test_delete_no_exports_services_snaps(self):
        # happy path

        share = Share.objects.get(name="root-share")  # no associated exports/services
        sId = share.id

        # Delete share

        response7 = self.client.delete("{}/{}".format(self.BASE_URL, sId))
        self.assertEqual(response7.status_code, status.HTTP_200_OK, msg=response7.data)

    def test_delete_rock_ons_root(self):
        # unhappy paths

        # Delete share used by rock-on service
        share = Share.objects.get(name="rock-ons-root")  # from fixture - rock-ons-root
        sId = share.id

        # Delete share that is in use by rock-ons service
        e_msg = (
            "Share ({}) cannot be deleted because it is in use "
            "by the Rock-on service. To override this block select "
            "the force checkbox and try again.".format(share.name)
        )
        response8 = self.client.delete("{}/{}".format(self.BASE_URL, sId))
        self.assertEqual(
            response8.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response8.data,
        )
        self.assertEqual(response8.data[0], e_msg)

    def test_delete_os_exception(self):
        # Delete share mocking OS exception
        share = Share.objects.get(name="root-share")  # no associated exports/services
        sId = share.id  # from fixture - rock-ons-root

        e_msg = "Failed to delete the share (root-share). Error from the OS: "

        self.mock_remove_share.side_effect = Exception

        response = self.client.delete("{}/{}".format(self.BASE_URL, sId))
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

        self.mock_remove_share.side_effect = None
