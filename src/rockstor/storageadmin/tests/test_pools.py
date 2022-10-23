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
from mock import patch

import fs.btrfs
from storageadmin.models import Disk, Pool, PoolBalance
from storageadmin.tests.test_api import APITestMixin

"""
Fixture creation instructions:

System needs 7 virtio data disks (min 5 GB). Maintain system pool.

- Virtio disk serial '1'
- Virtio disk serial '2'
- Virtio disk serial '3'
- Virtio disk serial '4'
- Virtio disk serial '5'
- Virtio disk serial '6'
- Virtio disk serial '7' (for 'existing-pool')

- Create 'existing-pool' using btrfs-raid 'single' with virtio disk serial '7'
- Create 'existing-share' on 'existing-pool'

bin/django dumpdata storageadmin.pool storageadmin.disk storageadmin.share \
--natural-foreign --indent 4 > \
src/rockstor/storageadmin/fixtures/test_pools.json

./bin/test -v 2 -p test_pools.py
"""


class PoolTests(APITestMixin):
    fixtures = ["test_api.json", "test_pools.json"]
    BASE_URL = "/api/pools"
    default_balance_status = {"status": "finished", "percent_done": 100}

    @classmethod
    def setUpClass(cls):
        super(PoolTests, cls).setUpClass()

        # post mocks
        # We redirect all btrfs commands to a fake-pool mount point.
        cls.patch_mount_root = patch("storageadmin.views.pool.mount_root")
        cls.mock_mount_root = cls.patch_mount_root.start()
        cls.mock_mount_root.return_value = "/mnt2/fake-pool"

        cls.patch_add_pool = patch("storageadmin.views.pool.add_pool")
        cls.mock_add_pool = cls.patch_add_pool.start()
        cls.mock_add_pool.return_value = True

        cls.patch_btrfs_uuid = patch("storageadmin.views.pool.btrfs_uuid")
        cls.mock_btrfs_uuid = cls.patch_btrfs_uuid.start()
        cls.mock_btrfs_uuid.return_value = "bar"

        # Mock our resize pool command generator to return bash null command of "true"
        cls.patch_resize_pool = patch("storageadmin.views.pool.resize_pool_cmd")
        cls.mock_resize_pool = cls.patch_resize_pool.start()
        cls.mock_resize_pool.return_value = ["true"]

        # Mock our balance pool command generator to return bash null command of "true"
        cls.patch_balance_pool = patch("storageadmin.views.pool.balance_pool_cmd")
        cls.mock_balance_pool = cls.patch_balance_pool.start()
        cls.mock_balance_pool.return_value = ["true"]

        # delete mocks
        cls.patch_umount_root = patch("storageadmin.views.pool.umount_root")
        cls.mock_umount_root = cls.patch_umount_root.start()
        cls.mock_umount_root.return_value = True

        # remount mocks
        cls.patch_remount = patch("storageadmin.views.pool.remount")
        cls.mock_remount = cls.patch_remount.start()
        cls.mock_remount.return_value = True

        # mock Pool.free model @property calculation from fs/btrfs.py pool_usage().
        cls.patch_pool_usage = patch("storageadmin.models.pool.pool_usage")
        cls.mock_pool_usage = cls.patch_pool_usage.start()
        cls.mock_pool_usage.return_value = 0

        # mock Pool mount status to always return True, this side steps many reports of:
        # "Pool member / raid edits require an active mount.  Please see the
        # "Maintenance required" section." i.e. pr #2010 on GitHub.
        cls.patch_mount_status = patch("storageadmin.models.pool.mount_status")
        cls.mock_mount_status = cls.patch_mount_status.start()
        cls.mock_mount_status.return_value = True

        # Mock balance_status() - Wrapper for 'btrfs balance status pool_mount_point'.
        # For testing our response to PUT add command (adding disks and/or re-raid).
        cls.patch_balance_status = patch("fs.btrfs.balance_status")
        cls.mock_balance_status = cls.patch_balance_status.start()
        cls.mock_balance_status.return_value = cls.default_balance_status


    @classmethod
    def tearDownClass(cls):
        super(PoolTests, cls).tearDownClass()

    def test_get(self):
        """
        Test GET request
        - Get base URL
        - Get existing pool
        - Get non-existent pool
        """
        self.get_base(self.BASE_URL)

        pool = Pool.objects.get(name="existing-pool")  # has 'existing-share'
        pId = pool.id

        # Get existing pool
        response = self.client.get("{}/{}".format(self.BASE_URL, pId))
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response)

        # get non-existing pool
        pId = 99999
        response = self.client.get("{}/{}".format(self.BASE_URL, pId))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, msg=response)

    def test_invalid_post_requests_name_clash(self):
        """
        invalid pool api operations
        - Create a pool with the same name as an existing share
        - Create a pool with the same name as an existing pool
        TODO - Create a pool with same name as an UN-IMPORTED existing pool
        """

        # create a pool with same name as an existing share

        existing_share_name = "existing-share"  # in fixture on system pool.
        data = {
            "disks": ("virtio-1", "virtio-2"),
            "pname": "{}".format(existing_share_name),
            "raid_level": "raid0",
        }
        e_msg = (
            "A share with this name ({}) exists. Pool and share "
            "names must be distinct. "
            "Choose a different name.".format(existing_share_name)
        )
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

        # Create a pool with same name as an existing pool

        existing_pool_name = "existing-pool"  # in fixture.
        data["pname"] = existing_pool_name
        e_msg = "Pool ({}) already exists. Choose a different name.".format(
            existing_pool_name
        )
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

    def test_invalid_post_requests_raid_level(self):
        """
        - Create a pool with invalid raid level
        TODO Extend after we support raid1c3, raid1c4, and mixed raid levels across
        data and metadata.
        """

        # create pool with invalid raid level
        data = {
            "disks": ("virtio-1", "virtio-2"),
            "pname": "invalid-raid-level",
            "raid_level": "derp",
        }
        e_msg = (
            "Unsupported raid level. Use one of: "
            "('single', 'raid0', 'raid1', 'raid10', 'raid5', 'raid6')."
        )
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

    def test_invalid_put_requests_nonexistent_disk(self):
        """
        - add non-existent disk to existing pool
        - TODO add disk with existing btrfs_uuid (i.e. has existing btrfs fs)
        """

        pool = Pool.objects.get(name="existing-pool")  # has 'existing-share'
        pId = pool.id
        invalid_disk_id = 99999

        # add non-existent disk to existing pool
        data = {"disks": ("{}".format(invalid_disk_id),)}
        e_msg = "Disk with id ({}) does not exist.".format(invalid_disk_id)
        response = self.client.put("{}/{}/add".format(self.BASE_URL, pId), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

        # add disk with existing btrfs_uuid

    def test_invalid_put_requests_command(self):

        # invalid put command
        pool = Pool.objects.get(name="existing-pool")  # has 'existing-share'
        pId = pool.id

        e_msg = "Command (invalid-command) is not supported."
        response5 = self.client.put("{}/{}/invalid-command".format(self.BASE_URL, pId))
        self.assertEqual(
            response5.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response5.data,
        )
        self.assertEqual(response5.data[0], e_msg)

    def test_put_requests_add_remove_disks(self):
        """
        Test disk add/remove on an existing pool
        - add 2 disks to existing pool.
        - remove 2 disks from existing pool
        """

        existing_pool = Pool.objects.get(name="existing-pool")  # has 'existing-share'
        pId = existing_pool.id

        # class MockPoolBalance(PoolBalance):
        #     """
        #     A mocked PoolBalance to enable fake status
        #     """
        #     def __init__(self, *args, **kwargs):
        #         super(PoolBalance, self).__init__(*args, **kwargs)
        #     def save(self):
        #         # We override our parent save
        #         # started|running|cancelling|cancelled|
        #         # pausing|paused|finished|failed|terminated
        #         self.status = "finished"
        #         super(PoolBalance, self)
        # temp_mock_PoolBalance = MockPoolBalance(status="finished")
        # mock_PoolBalance.objects.get.side_effect = temp_mock_PoolBalance

        # add 2 disks to existing pool.
        add_disk1_id = Disk.objects.get(name="virtio-5").id
        add_disk2_id = Disk.objects.get(name="virtio-6").id

        data_2_disks = {"disks": ("{}".format(add_disk1_id), "{}".format(add_disk2_id))}
        response = self.client.put(
            "{}/{}/add".format(self.BASE_URL, pId), data=data_2_disks
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        # We don't background 'add' so no Huey task and we just add to db directly.
        self.assertEqual(len(response.data["disks"]), 3)

        # remove 2 disks from existing pool
        response = self.client.put(
            "{}/{}/remove".format(self.BASE_URL, pId), data=data_2_disks
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        # Remove is done via a Huey back-ground task (unless all pool disk detached).
        # We then rely on bottom up btrfs commands to inform our pool info of the
        # drives removed at scan time so we can't do the following without first
        # mocking our btrfs informer commands.
        # self.assertEqual(len(response.data["disks"]), 1)
        #

    def test_invalid_requests_nonexistent_pool(self):
        """
        invalid pool api operations
        - edit non-existent pool
        - delete non-existent pool
        """

        # edit non-existent pool
        data = {"disks": ("virtio-1", "virtio-2")}
        pId = 99999
        e_msg = "Pool with id ({}) does not exist.".format(pId)
        response = self.client.put("{}/{}/add".format(self.BASE_URL, pId), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

        # delete non-existent pool
        response = self.client.delete("{}/{}".format(self.BASE_URL, pId))
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

    def test_invalid_root_pool_edits(self):
        """
        - add disk to root pool
        - delete root pool
        """

        # add disk to root pool
        pool = Pool.objects.get(name="ROOT")  # fixture system pool
        pId = pool.id

        # TODO use valid disk id, disk names are post only now.
        data = {"disks": ("virtio-1",)}
        e_msg = (
            "Edit operations are not allowed on this "
            "pool ({}) as it contains the operating "
            "system."
        ).format(pool.name)
        response = self.client.put("{}/1/add".format(self.BASE_URL, pId), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

        # delete root pool
        e_msg = (
            "Deletion of pool ({}) is not allowed as it "
            "contains the operating system."
        ).format(pool.name)
        response = self.client.delete("{}/{}".format(self.BASE_URL, pId))
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

    def test_name_regex(self):
        """
        1. Test some valid pool names
        2. Test some invalid pool names
        3. Empty string for pool name
        4. max length(255 character) for pool name
        5. max length + 1 for pool name
        """

        # valid pool names
        data = {"disks": ("virtio-2",), "raid_level": "single"}
        valid_names = (
            "123pool",
            "POOL_TEST",
            "Zzzz...",
            "1234",
            "mypool",
            "P" + "o" * 253 + "l",
        )
        for pname in valid_names:
            data["pname"] = pname
            response = self.client.post(self.BASE_URL, data=data)
            self.assertEqual(
                response.status_code, status.HTTP_200_OK, msg=response.data
            )
            self.assertEqual(response.data["name"], pname)

        # invalid pool names
        # TODO: Test needs updating:
        e_msg = (
            "Invalid characters in pool name. Following "
            "characters are allowed: letter(a-z or A-Z), "
            "digit(0-9), "
            "hyphen(-), underscore(_) or a period(.)."
        )
        # The invalid_pool_names list is based on above description, some are
        # POSIX valid but ruled out as less portable.
        invalid_pool_names = (
            "Pool 1",
            "Pa$sign",
            "/pool",
            ":pool",
            "\pool",
            "Pquestion?mark",
            "Pasteri*",
            "",
            " ",
        )

        for pname in invalid_pool_names:
            data["pname"] = pname
            response = self.client.post(self.BASE_URL, data=data)
            self.assertEqual(
                response.status_code,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                msg=response.data,
            )
            self.assertEqual(response.data[0], e_msg)

        # pool name with more than 255 characters
        e_msg = "Pool name must be less than 255 characters."

        data["pname"] = "P" + "o" * 254 + "l"
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

    def test_compression(self):
        """
        Compression is agnostic to name, raid and number of disks. So no
        need to test it with different types of pools. Every post & remount
        calls this.
        - Create a pool with invalid compression
        - Create a pool with zlib compression - compression-test-pool
        - change from zlib to lzo
        - Create a pool with no compression - compression-test-pool2
        - change from no to lzo
        - change from lzo to zlib
        - disable zlib
        - enable zlib
        - disable lzo - compression-test-pool
        - enable lzo
        """

        # create pool with invalid compression
        data = {
            "disks": ("virtio-1", "virtio-2"),
            "pname": "compression-test-pool",
            "raid_level": "single",
            "compression": "derp",
        }
        e_msg = (
            "Unsupported compression algorithm (derp). "
            "Use one of ('lzo', 'zlib', 'no')."
        )
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

        # create pool with zlib compression
        data["compression"] = "zlib"
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["compression"], "zlib")

        pool = Pool.objects.get(name="compression-test-pool")  # just created above
        pId = pool.id

        # change compression from zlib to lzo
        comp_lzo = {"compression": "lzo"}
        response = self.client.put(
            "{}/{}/remount".format(self.BASE_URL, pId), data=comp_lzo
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["compression"], "lzo")

        # Leave this pool for a bit at lzo.

        # create another pool with no compression
        data2 = {
            "disks": ("virtio-3", "virtio-4"),
            "pname": "compression-test-pool2",
            "raid_level": "single",
        }
        response = self.client.post(self.BASE_URL, data=data2)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["compression"], "no")

        temp_pool2 = Pool.objects.get(name="compression-test-pool2")
        pId2 = temp_pool2.id

        # change compression from no to lzo compression-test-pool2
        response = self.client.put(
            "{}/{}/remount".format(self.BASE_URL, pId2), data=comp_lzo
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["compression"], "lzo")

        # change compression from lzo to zlib compression-test-pool2
        comp_zlib = {"compression": "zlib"}
        # call remount pool command with new compression setting request (put)
        response = self.client.put(
            "{}/{}/remount".format(self.BASE_URL, pId2), data=comp_zlib
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["compression"], "zlib")

        # disable zlib compression compression-test-pool2
        comp_no = {"compression": "no"}
        response = self.client.put(
            "{}/{}/remount".format(self.BASE_URL, pId2), data=comp_no
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["compression"], "no")

        # enable zlib compression compression-test-pool2
        response = self.client.put(
            "{}/{}/remount".format(self.BASE_URL, pId2), data=comp_zlib
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["compression"], "zlib")

        # back to original compression-test-pool which was at lzo last

        # disable lzo compression compression-test-pool via remount put.
        response = self.client.put(
            "{}/{}/remount".format(self.BASE_URL, pId), data=comp_no
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["compression"], "no")

        # enable lzo compression again on compression-test-pool
        response = self.client.put(
            "{}/{}/remount".format(self.BASE_URL, pId), data=comp_lzo
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["compression"], "lzo")

    def test_mount_options(self):
        """
        Mount options are agnostic to other parameters such as compression.
        Mount validations are called every post & remount operation.
        - test invalid options (see allowed_options in the pool.py(view))
        -- (not including invalid compress-force see later)
        - test all valid mount options
        -- (not including valid compress-force see later)
        - test invalid compress-force options
        - test valide compress-force options
        """
        # We need this to construct our e_msg later
        allowed_options = {
            "alloc_start": int,
            "autodefrag": None,
            "clear_cache": None,
            "commit": int,
            "compress-force": settings.COMPRESSION_TYPES,
            "degraded": None,
            "discard": None,
            "fatal_errors": None,
            "inode_cache": None,
            "max_inline": int,
            "metadata_ratio": int,
            "noacl": None,
            "noatime": None,
            "nodatacow": None,
            "nodatasum": None,
            "nospace_cache": None,
            "nossd": None,
            "ro": None,
            "rw": None,
            "skip_balance": None,
            "space_cache": None,
            "ssd": None,
            "ssd_spread": None,
            "thread_pool": int,
            "": None,
        }

        # test invalid mount options
        data = {
            "disks": ("virtio-1", "virtio-2"),
            "pname": "mount-options-test-pool",
            "raid_level": "single",
            "compression": "zlib",
            "mnt_options": "alloc_star",
        }

        e_msg = (
            "mount option ({}) not allowed. Make sure there are "
            "no whitespaces in the input. Allowed options: "
            "({})."
        ).format(data["mnt_options"], sorted(allowed_options.keys()))

        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

        # valid alloc_start but without value
        data["mnt_options"] = "alloc_start"
        e_msg = "Value for mount option (alloc_start) must be an integer."
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

        # valid alloc_start with non integer value
        data["mnt_options"] = "alloc_start=derp"
        response3 = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response3.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response3.data,
        )
        self.assertEqual(response3.data[0], e_msg)

        # test all valid mount options

        # test fatal_errors option on its own
        data["mnt_options"] = "fatal_errors"
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["mnt_options"], "fatal_errors")
        self.assertEqual(response.data["compression"], "zlib")

        valid_mnt_options = (
            "alloc_start=3,autodefrag,clear_cache,commit=4,"
            "degraded,discard,fatal_errors,inode_cache,"
            "max_inline=2,metadata_ratio=5,noacl,noatime,"
            "nodatacow,nodatasum,nospace_cache,nossd,ro,"
            "rw,skip_balance,space_cache,ssd,ssd_spread,"
            "thread_pool=1"
        )

        # hacky as depends on above success in creating this pool.
        temp_pool = Pool.objects.get(name="mount-options-test-pool")
        pId = temp_pool.id

        # test all valid_mnt_options set applied simultaneously
        data2 = {"mnt_options": valid_mnt_options}
        response = self.client.put(
            "{}/{}/remount".format(self.BASE_URL, pId), data=data2
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["mnt_options"], valid_mnt_options)

        # test invalid compress-force applied via remount command
        data2 = {"mnt_options": "compress-force=1"}
        e_msg = "compress-force is only allowed with ('lzo', 'zlib', 'no')."
        response = self.client.put(
            "{}/{}/remount".format(self.BASE_URL, pId), data=data2
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

        # test compress-force options via remount command
        # when pool data not included in request, _validate_compression
        # sets compression to 'no' despite pool having a compression value
        # compress-force=no
        data2 = {"mnt_options": "compress-force=no"}
        response = self.client.put(
            "{}/{}/remount".format(self.BASE_URL, pId), data=data2
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["mnt_options"], "compress-force=no")
        self.assertEqual(response.data["compression"], "no")

        # compress-force=zlib
        data2 = {"mnt_options": "compress-force=zlib"}
        response = self.client.put(
            "{}/{}/remount".format(self.BASE_URL, pId), data=data2
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["mnt_options"], "compress-force=zlib")
        self.assertEqual(response.data["compression"], "no")

        # compress-force=lzo
        data2 = {"mnt_options": "compress-force=lzo"}
        response = self.client.put(
            "{}/{}/remount".format(self.BASE_URL, pId), data=data2
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["mnt_options"], "compress-force=lzo")
        self.assertEqual(response.data["compression"], "no")

    def test_single_crud(self):
        """
        CRUD = Create Read Update Delete
        test pool crud ops with 'single' raid config.
        Btrfs-single can be used to create a pool with 1 or more drives.
        - create a pool with 0 disks
        - create a pool with 1 disk
        - create a pool with 2 disks
        TODO - add a disk that already belongs to pool
        - add a disk that already belongs to another pool
        - remove disk that doesn't belong to pool
        - delete pool
        """

        # create pool with 0 disks
        data = {"pname": "singlepool", "raid_level": "single"}
        # TODO This is not a good user error message:
        e_msg = "'NoneType' object is not iterable"
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

        # create pool with 1 disk
        data["disks"] = ("virtio-2",)
        response2 = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response2.status_code, status.HTTP_200_OK, msg=response2.data)
        self.assertEqual(response2.data["name"], "singlepool")
        self.assertEqual(response2.data["raid"], "single")
        self.mock_btrfs_uuid.assert_called_with("virtio-2")
        self.assertEqual(len(response2.data["disks"]), 1)

        # create pool with 2 disks
        data = {
            "disks": ("virtio-3", "virtio-4"),
            "pname": "singlepool2",
            "raid_level": "single",
        }
        response3 = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response3.status_code, status.HTTP_200_OK, msg=response3.data)
        self.assertEqual(response3.data["name"], "singlepool2")
        self.assertEqual(response3.data["raid"], "single")
        self.assertEqual(len(response3.data["disks"]), 2)

        other_pool_member = Disk.objects.get(name="virtio-2")

        singlepool2 = Pool.objects.get(name="singlepool2")  # created earlier in test
        sp2Id = singlepool2.id

        # TODO remove disk that doesn't belong to pool

        # add a disk that already belongs to another pool
        data4 = {"disks": ("{}".format(other_pool_member.id),)}
        e_msg = (
            "Disk ({}) cannot be added to this pool ({}) "
            "because it belongs to another pool (singlepool).".format(
                other_pool_member.name, singlepool2.name
            )
        )
        response6 = self.client.put(
            "{}/{}/add".format(self.BASE_URL, sp2Id), data=data4
        )
        self.assertEqual(
            response6.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response6.data,
        )
        self.assertEqual(response6.data[0], e_msg)

        # delete singlepool2

        response = self.client.delete("{}/{}".format(self.BASE_URL, sp2Id))
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.mock_umount_root.assert_called_with("/mnt2/singlepool2")

    def test_raid0_crud(self):
        """
        CRUD = Create Read Update Delete
        test pool crud ops with 'raid0' raid config. Raid0 can be used to
        create a pool with at least 2 disks (we currently do not allow removal):
        - atempt to create a pool with 1 disk
        - create a pool with 2 disks
        - get pool
        - add one disk to pool
        - attempt to remove one disk from pool (two after #2385)
        - attempt to add 3 disks & change raid_level from raid0 to raid1
        -- (set PoolBalance for temp_pool to have "finished" status)
        - retry add 3 disks & change raid_level from raid0 to raid1
        - delete pool
        """
        # Establish our id references, not all used but once we have moved to
        # disk id for POST calls they will all be needed.
        virtio_1_id = Disk.objects.get(name="virtio-1").id
        virtio_2_id = Disk.objects.get(name="virtio-2").id
        virtio_3_id = Disk.objects.get(name="virtio-3").id
        virtio_4_id = Disk.objects.get(name="virtio-4").id
        virtio_5_id = Disk.objects.get(name="virtio-5").id
        virtio_6_id = Disk.objects.get(name="virtio-6").id
        virtio_7_id = Disk.objects.get(name="virtio-7").id

        data = {"disks": ("virtio-1",), "pname": "raid0pool", "raid_level": "raid0"}

        # attempt to create pool with 1 disk
        e_msg = "At least 2 disks are required for the raid level: raid0."
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

        # create a pool with 2 disks
        data["disks"] = ("virtio-1", "virtio-2")
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["name"], "raid0pool")
        self.assertEqual(response.data["raid"], "raid0")
        self.mock_btrfs_uuid.assert_called_with("virtio-1")
        self.assertEqual(len(response.data["disks"]), 2)

        temp_pool = Pool.objects.get(name="raid0pool")
        pId = temp_pool.id

        # get pool
        response = self.client.get("{}/{}".format(self.BASE_URL, pId))
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["name"], "raid0pool")

        # add one disk to pool
        data2 = {"disks": ("{}".format(virtio_3_id),)}
        response2 = self.client.put("{}/{}/add".format(self.BASE_URL, pId), data=data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK, msg=response2.data)
        self.assertEqual(len(response2.data["disks"]), 3)

        # attempt to remove one disk from pool (two after #2385)
        # TODO This test passes to prove our intended function.
        #  however our tested code intention (current behaviour) is up for review #2385
        response3 = self.client.put(
            "{}/{}/remove".format(self.BASE_URL, pId), data=data2
        )
        self.assertEqual(
            response3.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response3.data,
        )
        e_msg = (
            "Disks cannot be removed from a pool with this raid (raid0) "
            "configuration."
        )
        self.assertEqual(response3.data[0], e_msg)

        # attempt to add 3 disks & change raid_level from raid0 to raid1
        data3 = {
            "disks": (
                "{}".format(virtio_4_id),
                "{}".format(virtio_5_id),
                "{}".format(virtio_6_id),
            ),
            "raid_level": "raid1",
        }
        e_msg = (
            "A Balance process is already running or paused "
            "for this pool ({}). Resize is not supported "
            "during a balance process.".format(temp_pool.name)
        )
        response4 = self.client.put("{}/{}/add".format(self.BASE_URL, pId), data=data3)
        # Assert PoolBalance started state
        temp_PoolBalance = PoolBalance.objects.filter(pool=temp_pool).latest(
            "start_time"
        )
        a_msg = "PoolBalance status for pool expected to have state 'started'"
        self.assertEqual(temp_PoolBalance.status, "started", msg=a_msg)
        self.assertEqual(
            response4.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response4.data,
        )
        self.assertEqual(response4.data[0], e_msg)

        # set PoolBalance for temp_pool to have "finished" status
        temp_PoolBalance.refresh_from_db()
        temp_PoolBalance.status = "finished"
        temp_PoolBalance.save()

        # retry add 3 disks & change raid_level from raid0 to raid1
        response = self.client.put("{}/{}/add".format(self.BASE_URL, pId), data=data3)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["name"], "{}".format(temp_pool.name))
        self.assertEqual(len(response.data["disks"]), 6)
        # We ascertain pool raid level bottom up so would require btrfs fi show command
        # output mock followed by a pool refresh call.
        # self.assertEqual(response2.data["raid"], "raid1")

        # delete pool
        response5 = self.client.delete("{}/{}".format(self.BASE_URL, pId))
        self.assertEqual(response5.status_code, status.HTTP_200_OK, msg=response5.data)
        self.mock_umount_root.assert_called_with("/mnt2/raid0pool")

    def test_raid1_crud(self):
        """
        CRUD = Create Read Update Delete
        test pool crud ops with 'raid1' raid config. raid1 can be used to
        create a pool with 2 or more disks.
        - Attempt to create a btrfs-raid1 pool with 1 disk.
        - Create btrfs-raid1 pool with 2 disks.
        - Add 2 disks to pool.
        -  Remove disks where it would shrink the pool by greater than free space.
        -- Test removing a single disk: allocation > pool.free.
        -- Test removing two disks: allocation > pool.free.
        - Attempt removing three disks taking pool below minimum drive count.
        - Migrate 'raid1' to 'raid10' and add one disk.
        - remove 1 disks
        - Migrate raid10 to raid1 adding zero disks via PUT add command.
        - delete pool
        """

        # Establish our id references, not all may be used but once we have moved to
        # disk id for POST calls they will all be needed.
        virtio_1 = Disk.objects.get(name="virtio-1")
        virtio_1_id = virtio_1.id
        virtio_2 = Disk.objects.get(name="virtio-2")
        virtio_2_id = virtio_2.id
        virtio_3_id = Disk.objects.get(name="virtio-3").id
        virtio_4_id = Disk.objects.get(name="virtio-4").id
        virtio_5_id = Disk.objects.get(name="virtio-5").id

        data = {"disks": ("virtio-1",), "pname": "raid1pool", "raid_level": "raid1"}

        # Attempt to create a btrfs-raid1 pool with 1 disk.
        e_msg = "At least 2 disks are required for the raid level: raid1."
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

        # Create btrfs-raid1 pool with 2 disks.
        data["disks"] = ("virtio-1", "virtio-2")
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["name"], "raid1pool")
        self.assertEqual(response.data["raid"], "raid1")
        self.mock_btrfs_uuid.assert_called_with("virtio-1")
        self.assertEqual(len(response.data["disks"]), 2)

        temp_pool = Pool.objects.get(name="raid1pool")
        pId = temp_pool.id

        # Add 2 disks.
        data2 = {"disks": ("{}".format(virtio_3_id), "{}".format(virtio_4_id))}
        response2 = self.client.put("{}/{}/add".format(self.BASE_URL, pId), data=data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK, msg=response2.data)
        self.assertEqual(len(response2.data["disks"]), 4)

        # Remove disks where it would shrink the pool by greater than free space.

        # Test removing a single disk: allocation > pool.free.
        # Pool size from now 4 fixture disk members of 5 GB each:
        # is 10485760 KB (4 * 5GB) / 2 as raid1).
        self.mock_pool_usage.return_value = 10485760 - 2000000  # 2000000 KB free
        virtio_1.refresh_from_db()
        virtio_1.allocated = 2000001
        virtio_1.save()
        data3 = {"disks": ("{}".format(virtio_1_id),)}
        response3 = self.client.put(
            "{}/{}/remove".format(self.BASE_URL, pId), data=data3
        )
        self.assertEqual(
            response3.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response3.data,
        )
        e_msg = (
            "Removing disk/s (virtio-1) may shrink the pool by "
            "2000001 KB, which is greater than available free "
            "space 2000000 KB. This is not supported."
        )
        self.assertEqual(response3.data[0], e_msg)

        # Test removing two disks: allocation > pool.free.
        virtio_2.refresh_from_db()
        virtio_2.allocated = 2000001
        virtio_2.save()
        data3 = {"disks": ("{}".format(virtio_1_id), "{}".format(virtio_2_id))}
        response3 = self.client.put(
            "{}/{}/remove".format(self.BASE_URL, pId), data=data3
        )
        self.assertEqual(
            response3.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response3.data,
        )
        e_msg = (
            "Removing disk/s (virtio-1 virtio-2) may shrink the pool by "
            "4000002 KB, which is greater than available free "
            "space 2000000 KB. This is not supported."
        )
        self.assertEqual(response3.data[0], e_msg)

        # Reset our mock return value as otherwise we contaminate tests run after us.
        self.mock_pool_usage.return_value = 0

        # Attempt removing three disks taking pool below minimum drive count.
        virtio_2.refresh_from_db()
        virtio_2.allocated = 1000001
        virtio_2.save()
        data3 = {
            "disks": (
                "{}".format(virtio_2_id),
                "{}".format(virtio_3_id),
                "{}".format(virtio_4_id),
            )
        }
        e_msg = (
            "Disks cannot be removed from this pool because its raid "
            "configuration (raid1) requires a minimum of 2 disks."
        )
        response4 = self.client.put(
            "{}/{}/remove".format(self.BASE_URL, pId), data=data3
        )
        self.assertEqual(
            response4.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response4.data,
        )
        self.assertEqual(response4.data[0], e_msg)

        # set PoolBalance for temp_pool to have "finished" status
        temp_PoolBalance = PoolBalance.objects.filter(pool=temp_pool).latest(
            "start_time"
        )
        temp_PoolBalance.refresh_from_db()
        temp_PoolBalance.status = "finished"
        temp_PoolBalance.save()

        #  Migrate raid1 to raid10 and add one disk.
        data5 = {"disks": ("{}".format(virtio_5_id),), "raid_level": "raid10"}
        response = self.client.put("{}/{}/add".format(self.BASE_URL, pId), data=data5)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["name"], "raid1pool")
        # this may be ascertained bottom up, so we would need to mock the
        # associated calls.
        # self.assertEqual(response4.data["raid"], "raid10")
        self.assertEqual(len(response.data["disks"]), 5)

        # set PoolBalance for temp_pool to have "finished" status
        temp_PoolBalance = PoolBalance.objects.filter(pool=temp_pool).latest(
            "start_time"
        )
        temp_PoolBalance.refresh_from_db()
        temp_PoolBalance.status = "finished"
        temp_PoolBalance.save()

        # remove 1 disks
        data2 = {"disks": ("{}".format(virtio_5_id),)}
        response3 = self.client.put(
            "{}/{}/remove".format(self.BASE_URL, pId), data=data2
        )
        self.assertEqual(response3.status_code, status.HTTP_200_OK, msg=response3.data)
        # Remove is done via a Huey back-ground task (unless all pool disk detached).
        # We then rely on bottom up btrfs commands to inform our pool info of the
        # drives removed at scan time so we can't do the following without first
        # mocking our btrfs informer commands.
        # self.assertEqual(len(response3.data["disks"]), 3)

        # set PoolBalance for temp_pool to have "finished" status
        temp_PoolBalance = PoolBalance.objects.filter(pool=temp_pool).latest(
            "start_time"
        )
        temp_PoolBalance.refresh_from_db()
        temp_PoolBalance.status = "finished"
        temp_PoolBalance.save()

        # Migrate raid10 to raid1 adding zero disks via PUT add command.
        data5 = {"disks": [], "raid_level": "raid1"}
        response = self.client.put("{}/{}/add".format(self.BASE_URL, pId), data=data5)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["name"], "raid1pool")
        # this may be ascertained bottom up, so we would need to mock the
        # associated calls.
        # self.assertEqual(response4.data["raid"], "raid1")

        # delete pool
        response5 = self.client.delete("{}/{}".format(self.BASE_URL, pId))
        self.assertEqual(response5.status_code, status.HTTP_200_OK, msg=response5.data)
        self.mock_umount_root.assert_called_with("/mnt2/raid1pool")

    def test_raid10_crud(self):
        """
        CRUD = Create Read Update Delete
        test pool crud ops with 'raid10' raid config. Raid10 can be used to
        create a pool with at least 4 disks.
        - Create pool with 3 disk.
        - Create pool with 4 disks.
        - Add 2 disks to bring total to 6.
        - Remove 3 disks reducing drive count below btrfs-raid level10 minimum.
        - Remove 1 disk.
        - Delete pool.
        """

        # Establish our id references, not all may be used but once we have moved to
        # disk id for POST calls they will all be needed.
        virtio_1 = Disk.objects.get(name="virtio-1")
        virtio_1_id = virtio_1.id
        virtio_2 = Disk.objects.get(name="virtio-2")
        virtio_2_id = virtio_2.id
        virtio_3_id = Disk.objects.get(name="virtio-3").id
        virtio_4_id = Disk.objects.get(name="virtio-4").id
        virtio_5_id = Disk.objects.get(name="virtio-5").id
        virtio_6_id = Disk.objects.get(name="virtio-6").id

        # Create pool with 3 disk.
        data = {
            "disks": ("virtio-1", "virtio-2", "virtio-3"),
            "pname": "raid10pool",
            "raid_level": "raid10",
        }
        e_msg = "A minimum of 4 drives are required for the raid level: raid10."
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

        # Create pool with 4 disks.
        data["disks"] = ("virtio-1", "virtio-2", "virtio-3", "virtio-4")
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["name"], "raid10pool")
        self.assertEqual(response.data["raid"], "raid10")
        self.mock_btrfs_uuid.assert_called_with("virtio-1")
        self.assertEqual(len(response.data["disks"]), 4)

        temp_pool = Pool.objects.get(name="raid10pool")
        pId = temp_pool.id

        # Add 2 disks to bring total to 6.
        data2 = {"disks": ("{}".format(virtio_5_id), "{}".format(virtio_6_id))}
        response = self.client.put("{}/{}/add".format(self.BASE_URL, pId), data=data2)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(len(response.data["disks"]), 6)

        # Remove 3 disks reducing drive count below btrfs-raid level10 minimum.
        data2 = {
            "disks": (
                "{}".format(virtio_4_id),
                "{}".format(virtio_5_id),
                "{}".format(virtio_6_id),
            )
        }
        response = self.client.put(
            "{}/{}/remove".format(self.BASE_URL, pId), data=data2
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = (
            "Disks cannot be removed from this pool because its raid "
            "configuration (raid10) requires a minimum of 4 disks."
        )
        self.assertEqual(response.data[0], e_msg)

        # Remove 1 disk.
        data = {"disks": ("{}".format(virtio_1_id),)}
        response = self.client.put("{}/{}/remove".format(self.BASE_URL, pId), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        # Remove is done via a Huey back-ground task (unless all pool disk detached).
        # We then rely on bottom up btrfs commands to inform our pool info of the
        # drives removed at scan time so we can't do the following without first
        # mocking our btrfs informer commands.
        # self.assertEqual(len(response3.data["disks"]), 5)

        # Delete pool.
        response = self.client.delete("{}/{}".format(self.BASE_URL, pId))
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.mock_umount_root.assert_called_with("/mnt2/raid10pool")

    def test_raid5_crud(self):
        """
        CRUD = Create Read Update Delete
        Test pool crud ops with 'raid5' config.
        Btrfs-raid5 can be used to create a pool with 2 or more disks.
        - Create pool with 1 disk.
        - Create pool with 2 disks.
        - Add 2 disks.
        - Remove three disks so total < raid level minimum.
        - Remove 1 disk.
        - Delete pool
        """

        # Establish our id references, not all may be used but once we have moved to
        # disk id for POST calls they will all be needed.
        virtio_1 = Disk.objects.get(name="virtio-1")
        virtio_1_id = virtio_1.id
        virtio_2 = Disk.objects.get(name="virtio-2")
        virtio_2_id = virtio_2.id
        virtio_3_id = Disk.objects.get(name="virtio-3").id
        virtio_4_id = Disk.objects.get(name="virtio-4").id

        data = {"disks": ("virtio-1",), "pname": "raid5pool", "raid_level": "raid5"}

        # Create pool with 1 disk.
        e_msg = "2 or more disks are required for the raid level: raid5."
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

        # Create pool with 2 disks.
        data["disks"] = ("virtio-1", "virtio-2")
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["name"], "raid5pool")
        self.assertEqual(response.data["raid"], "raid5")
        self.mock_btrfs_uuid.assert_called_with("virtio-1")
        self.assertEqual(len(response.data["disks"]), 2)

        temp_pool = Pool.objects.get(name="raid5pool")
        pId = temp_pool.id

        # Add 2 disks.
        data2 = {"disks": ("{}".format(virtio_3_id), "{}".format(virtio_4_id))}
        response = self.client.put("{}/{}/add".format(self.BASE_URL, pId), data=data2)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(len(response.data["disks"]), 4)

        # Remove three disks so total < raid level minimum.
        data2 = {
            "disks": (
                "{}".format(virtio_2_id),
                "{}".format(virtio_3_id),
                "{}".format(virtio_4_id),
            )
        }
        response = self.client.put(
            "{}/{}/remove".format(self.BASE_URL, pId), data=data2
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = (
            "Disks cannot be removed from this pool because its raid "
            "configuration (raid5) requires a minimum of 2 disks."
        )
        self.assertEqual(response.data[0], e_msg)

        # Remove 1 disk.
        data = {"disks": ("{}".format(virtio_1_id),)}
        response = self.client.put("{}/{}/remove".format(self.BASE_URL, pId), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        # Remove is done via a Huey back-ground task (unless all pool disk detached).
        # We then rely on bottom up btrfs commands to inform our pool info of the
        # drives removed at scan time so we can't do the following without first
        # mocking our btrfs informer commands.
        # self.assertEqual(len(response3.data["disks"]), 5)

        # Delete pool
        response = self.client.delete("{}/{}".format(self.BASE_URL, pId))
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.mock_umount_root.assert_called_with("/mnt2/raid5pool")

    def test_raid6_crud(self):
        """
        CRUD = Create Read Update Delete
        Test pool crud ops with 'raid6' config.
        btrfs-raid6 can be used to create a pool with 3 or more disks.
        - Create pool with 1 disk.
        - Create pool with 3 disks.
        - Add 2 disks.
        - Remove three disks so total < raid level minimum.
        - Remove 1 disk.
        - Delete pool.
        """

        # Establish our id references, not all may be used but once we have moved to
        # disk id for POST calls they will all be needed.
        virtio_1 = Disk.objects.get(name="virtio-1")
        virtio_1_id = virtio_1.id
        virtio_2 = Disk.objects.get(name="virtio-2")
        virtio_2_id = virtio_2.id
        virtio_3_id = Disk.objects.get(name="virtio-3").id
        virtio_4_id = Disk.objects.get(name="virtio-4").id
        virtio_5_id = Disk.objects.get(name="virtio-5").id

        # Create pool with 1 disk.
        data = {"disks": ("virtio-1",), "pname": "raid6pool", "raid_level": "raid6"}
        e_msg = "3 or more disks are required for the raid level: raid6."
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

        # Create pool with 3 disks.
        data["disks"] = ("virtio-1", "virtio-2", "virtio-3")
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["name"], "raid6pool")
        self.assertEqual(response.data["raid"], "raid6")
        self.mock_btrfs_uuid.assert_called_with("virtio-1")
        self.assertEqual(len(response.data["disks"]), 3)

        # instantiate pool object so we can get its id
        temp_pool = Pool.objects.get(name="raid6pool")
        pId = temp_pool.id

        # Add 2 disks.
        data2 = {"disks": ("{}".format(virtio_4_id), "{}".format(virtio_5_id))}
        response2 = self.client.put("{}/{}/add".format(self.BASE_URL, pId), data=data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK, msg=response2.data)
        self.mock_btrfs_uuid.assert_called_with("virtio-1")
        self.assertEqual(len(response2.data["disks"]), 5)

        # Remove three disks so total < raid level minimum.
        data = {
            "disks": (
                "{}".format(virtio_3_id),
                "{}".format(virtio_4_id),
                "{}".format(virtio_5_id),
            )
        }
        response = self.client.put("{}/{}/remove".format(self.BASE_URL, pId), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = (
            "Disks cannot be removed from this pool because its raid "
            "configuration (raid6) requires a minimum of 3 disks."
        )
        self.assertEqual(response.data[0], e_msg)

        # Remove 1 disk.
        data = {"disks": ("{}".format(virtio_1_id),)}
        response = self.client.put("{}/{}/remove".format(self.BASE_URL, pId), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        # Remove is done via a Huey back-ground task (unless all pool disk detached).
        # We then rely on bottom up btrfs commands to inform our pool info of the
        # drives removed at scan time so we can't do the following without first
        # mocking our btrfs informer commands.
        # self.assertEqual(len(response3.data["disks"]), 4)

        # Delete pool.
        response = self.client.delete("{}/{}".format(self.BASE_URL, pId))
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.mock_umount_root.assert_called_with("/mnt2/raid6pool")

    def test_raid_migration_fencing_remove_command(self):
        """
        Test restrictions on raid change during PUT remove operations.
        At time of test construction we block all raid changes during disk removal.
        This is currently an overarching fence (read check performed).
        """

        virtio_7_id = Disk.objects.get(name="virtio-7").id  # existing-pool member

        existing_pool = Pool.objects.get(name="existing-pool")  # has 'existing-share'
        pId = existing_pool.id

        # Get existing pool and confirm single with 1 disk
        response = self.client.get("{}/{}".format(self.BASE_URL, pId))
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response)
        self.assertEqual(response.data["name"], "existing-pool")
        self.assertEqual(response.data["raid"], "single")
        self.assertEqual(len(response.data["disks"]), 1)

        # Invalid remove 1 disk & change raid_level.
        e_msg = "Raid configuration cannot be changed while removing disks."
        data = {"disks": ("{}".format(virtio_7_id),), "raid_level": "raid0"}
        response = self.client.put("{}/{}/remove".format(self.BASE_URL, pId), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

    def test_raid_migration_fencing_add_command(self):
        """
        Test raid migrations that we fence against in PUT add command
        - Invalid migrate single to raid5 with total disks < 2.
        - Add 3 disk & change raid_level from single to raid10.
        - Create raid1 pool with 2 disks.
        - Invalid migrate raid to raid5 with total disks < 2.
        - Invalid migrate raid1 to raid6 with total disks < 3.
        - Migrate 'raid1' to 'raid10' and specify 2 more disks.
        """

        # Establish our id references, not all may be used but once we have moved to
        # disk id for POST calls they will all be needed.
        virtio_1 = Disk.objects.get(name="virtio-1")
        virtio_1_id = virtio_1.id
        virtio_2 = Disk.objects.get(name="virtio-2")
        virtio_2_id = virtio_2.id
        virtio_3_id = Disk.objects.get(name="virtio-3").id
        virtio_4_id = Disk.objects.get(name="virtio-4").id
        virtio_5_id = Disk.objects.get(name="virtio-5").id
        virtio_6_id = Disk.objects.get(name="virtio-6").id

        existing_pool = Pool.objects.get(name="existing-pool")  # has 'existing-share'
        pId = existing_pool.id

        # Get existing pool and confirm single with 1 disk
        response = self.client.get("{}/{}".format(self.BASE_URL, pId))
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response)
        self.assertEqual(response.data["name"], "existing-pool")
        self.assertEqual(response.data["raid"], "single")
        self.assertEqual(len(response.data["disks"]), 1)

        # Invalid migrate from single to raid5 with total disks < 2.
        e_msg = "A minimum of 2 drives are required for the raid level: raid5."
        data5 = {"disks": [], "raid_level": "raid5"}
        response = self.client.put("{}/{}/add".format(self.BASE_URL, pId), data=data5)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

        # Add 3 disks & change raid_level from single to raid10.
        # TODO: Consider removing once we have better space calc.
        #  Avoid extreme raid level change upwards (space issues).
        new_raid = "raid10"
        e_msg = ("Pool migration from {} to {} is not supported.").format(
            existing_pool.raid, new_raid
        )
        data2 = {
            "disks": (
                "{}".format(virtio_1_id),
                "{}".format(virtio_2_id),
                "{}".format(virtio_3_id),
            ),
            "raid_level": "raid10",
        }
        response4 = self.client.put("{}/{}/add".format(self.BASE_URL, pId), data=data2)
        self.assertEqual(
            response4.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response4.data,
        )
        self.assertEqual(response4.data[0], e_msg)

        # Create 'raid1' pool with 2 disks.
        data4 = {
            "disks": ("virtio-1", "virtio-2"),
            "pname": "raid1pool",
            "raid_level": "raid1",
        }
        response = self.client.post(self.BASE_URL, data=data4)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["name"], "raid1pool")
        self.assertEqual(response.data["raid"], "raid1")
        self.mock_btrfs_uuid.assert_called_with("virtio-1")
        self.assertEqual(len(response.data["disks"]), 2)

        # instantiate pool object so we can get its id
        temp_pool2 = Pool.objects.get(name="raid1pool")
        pId2 = temp_pool2.id

        # Invalid migrate 'raid1' to 'raid10' with total disks < 4.
        e_msg = "A minimum of 4 drives are required for the raid level: raid10."
        data5 = {"disks": ("{}".format(virtio_3_id),), "raid_level": "raid10"}
        response4 = self.client.put("{}/{}/add".format(self.BASE_URL, pId2), data=data5)
        self.assertEqual(
            response4.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response4.data,
        )
        self.assertEqual(response4.data[0], e_msg)

        # Invalid migrate from raid1 to raid6 with total disks < 3.
        e_msg = "A minimum of 3 drives are required for the raid level: raid6."
        data5 = {"disks": [], "raid_level": "raid6"}
        response4 = self.client.put("{}/{}/add".format(self.BASE_URL, pId2), data=data5)
        self.assertEqual(
            response4.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response4.data,
        )
        self.assertEqual(response4.data[0], e_msg)

    def test_delete_pool_with_share(self):
        # delete pool that has a share
        pool = Pool.objects.get(name="existing-pool")  # has 'existing-share'
        pId = pool.id
        e_msg = (
            "Pool ({}) is not empty. Delete is not allowed until all "
            "shares in the pool are deleted."
        ).format(pool.name)
        response = self.client.delete("{}/{}".format(self.BASE_URL, pId))
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)

    def test_balance_in_progress_fencing(self):
        """
        We block any balance or ReRaid if there are pending Huey tasks with:
        name matching "start_balance", "start_resize_pool"
        See model: storageadmin/models/pool_balance.py
        And View: storageadmin/views/pool_balance.py
        The PoolBalance model is used to interface with Huey in this regard.
        Huey is the library we use to run Balance jobs on another thread.
        Mocking required:
        balance_status(pool) for disk add we initiate a regular balance.
        balance_status_internal(pool) disk remove initiates an 'internal' balance

        N.B. in the following our Huey task could fail and update, via task.py,
        the status of the balance: (Pending code).

        # Check for block against ongoing cli initiated balance
        - Mock balance_status() to return status 'running'
        -- Initiate a regular balance via PUT add disk.
        --- Assert we are blocked by ongoing balance for this pool.

        Test reflection of real Pool balance status, i.e. we account for cli initiated
        balance.

        - Mock balance_status() to return status 'finished'
        -- Initiate a regular balance via PUT add disk.
        --- Assert PoolBalance reflects our mock
        - Mock balance_status_internal() to return status 'finished'
        -- Initiate an 'internal' balance via PUT remove disk.
        """

        # Establish our id references, not all may be used but once we have moved to
        # disk id for POST calls they will all be needed.
        virtio_1 = Disk.objects.get(name="virtio-1")
        virtio_1_id = virtio_1.id
        virtio_2 = Disk.objects.get(name="virtio-2")
        virtio_2_id = virtio_2.id
        virtio_3_id = Disk.objects.get(name="virtio-3").id
        virtio_4_id = Disk.objects.get(name="virtio-4").id
        virtio_5_id = Disk.objects.get(name="virtio-5").id
        virtio_6_id = Disk.objects.get(name="virtio-6").id

        existing_pool = Pool.objects.get(name="existing-pool")  # has 'existing-share'
        pId = existing_pool.id

        # Add disk to pool with cli initiated "running" balance status.
        e_msg = (
            "A Balance process is already running or paused "
            "for this pool ({}). Resize is not supported "
            "during a balance process.".format(existing_pool.name)
        )
        # mock and check mock of balance_status in fs.btrfs.balance_status
        # See fs.tests.test_btrfs.py for expected output from balance_status
        running_balance_status = {"status": "running", "percent_done": 6}
        self.mock_balance_status.return_value = running_balance_status
        result = fs.btrfs.balance_status(existing_pool)
        self.assertEqual(
            result,
            running_balance_status,
            msg=('Failed to confirm balance "running" mock status'),
        )

        one_disk = {"disks": ("{}".format(virtio_1_id),)}
        response = self.client.put(
            "{}/{}/add".format(self.BASE_URL, pId), data=one_disk
        )
        # Assert we have an error state returned and it's messages is what we expect
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], e_msg)
        # We don't background 'add' so no Huey task and we just add to db directly.
        # But in this case our above fail should mean we still have only one disk.
        # So get our pool info and check we still have only a single disk.
        response = self.client.get("{}/{}".format(self.BASE_URL, pId))
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response)
        self.assertEqual(len(response.data["disks"]), 1)
        # TODO the following should be assured by our setUpClass() but it is not.
        self.mock_balance_status.return_value = self.default_balance_status

