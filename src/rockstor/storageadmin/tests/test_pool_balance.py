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
from storageadmin.models import Pool, PoolBalance

"""
Fixture creation instructions:

System needs 1 non sys pool 'test-pool-balance', raid='raid1'). Maintain system pool.

- Virtio disk serial '1'  # for test-pool-balance
- Virtio disk serial '2'
- Virtio disk serial '3'

- Create 'test-pool-balance' using btrfs-raid 'single' with virtio disk serial '1'
- Enact two balance operations on 'test-pool-balance' and allow each to finish.

bin/django dumpdata storageadmin.pool storageadmin.disk storageadmin.poolbalance \
--natural-foreign --indent 4 > \
src/rockstor/storageadmin/fixtures/test_pool_balance.json

./bin/test -v 2 -p test_pool_balance.py
"""


class MockTask(object):
    id = 0


class PoolBalanceTests(APITestMixin):
    fixtures = ["test_api.json", "test_pool_balance.json"]
    BASE_URL = "/api/pools"
    default_balance_status = {"status": "finished", "percent_done": 100}
    default_balance_status_internal = {"status": "finished", "percent_done": 100}

    @classmethod
    def setUpClass(cls):
        super(PoolBalanceTests, cls).setUpClass()

        cls.patch_mount_root = patch("storageadmin.views.pool.mount_root")
        cls.mock_mount_root = cls.patch_mount_root.start()
        cls.mock_mount_root.return_value = "/mnt2/fake-pool"

        # Mock our balance pool command generator to return bash null command of "true"
        cls.patch_balance_pool = patch("storageadmin.views.pool.balance_pool_cmd")
        cls.mock_balance_pool = cls.patch_balance_pool.start()
        cls.mock_balance_pool.return_value = ["true"]

        # mock Pool mount status to always return True, this side steps many reports of:
        # "Pool member / raid edits require an active mount.  Please see the
        # "Maintenance required" section." i.e. pr #2010 on GitHub.
        cls.patch_mount_status = patch("storageadmin.models.pool.mount_status")
        cls.mock_mount_status = cls.patch_mount_status.start()
        cls.mock_mount_status.return_value = True

        # cls.patch_start_balance = patch("storageadmin.views.pool.start_balance")
        # cls.mock_start_balance = cls.patch_start_balance.start()
        # # start_balance normally returns a Huey task_result_handle.
        # cls.mock_start_balance.return_value = MockTask()

        # In the following two mocks we are preserving our ability to discern between
        # them. However, it should be noted that we also have a lower level test for
        # fs.btrfs.balance_status_all() that is a superset of:
        # - fs.btrfs.balance_status
        # - fs.btrfs.balance_status_internal
        # see fs/tests/btrfs.py test_balance_status_all()
        # As such we may want to move to mocking fs.btrfs.balance_status_all.

        # Mock balance_status() - Wrapper for 'btrfs balance status pool_mount_point'.
        # For testing our response to PUT add command (adding disks and/or re-raid).
        cls.patch_balance_status = patch("fs.btrfs.balance_status")
        cls.mock_balance_status = cls.patch_balance_status.start()
        cls.mock_balance_status.return_value = cls.default_balance_status

        # Mock balance_status_internal() - Wrapper for 'btrfs dev usage -b mnt_pt'.
        # For testing our response to PUT add command (adding disks and/or re-raid).
        cls.patch_balance_status_internal = patch("fs.btrfs.balance_status_internal")
        cls.mock_balance_status_internal = cls.patch_balance_status_internal.start()
        cls.mock_balance_status_internal.return_value = (
            cls.default_balance_status_internal
        )

    @classmethod
    def tearDownClass(cls):
        super(PoolBalanceTests, cls).tearDownClass()

    def test_get(self):

        test_pool = Pool.objects.get(name="test-pool-balance")  # has balance record
        pId = test_pool.id

        # get base URL
        response = self.client.get("{}/{}/balance".format(self.BASE_URL, pId))
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

    def test_post_invalid_pool(self):

        # invalid pool
        data = {"force": "true"}
        non_pId = 99999
        r = self.client.post("{}/{}/balance".format(self.BASE_URL, non_pId), data=data)
        self.assertEqual(
            r.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR, msg=r.data
        )

        e_msg = "Pool ({}) does not exist.".format(non_pId)
        self.assertEqual(r.data[0], e_msg)

    def test_post_valid_balance(self):

        test_pool = Pool.objects.get(name="test-pool-balance")  # has balance record
        pId = test_pool.id

        # happy path
        data = {"force": "true"}
        r = self.client.post("{}/{}/balance".format(self.BASE_URL, pId), data=data)
        self.assertEqual(r.status_code, status.HTTP_200_OK, msg=r.data)

    def test_post_invalid_balance_command(self):

        test_pool = Pool.objects.get(name="test-pool-balance")  # has balance record
        pId = test_pool.id

        # Invalid balance command
        data = {"force": "true"}
        r = self.client.post(
            "{}/{}/balance/invalid".format(self.BASE_URL, pId), data=data
        )
        self.assertEqual(
            r.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR, msg=r.data
        )

        e_msg = "Unknown balance command (invalid)."
        self.assertEqual(r.data[0], e_msg)

    def test_post_valid_status_command(self):

        # TODO Add behavioural test for {'status': 'unknown'} such as for
        #  unmounted volumes.
        #  and another series where we mock PoolBalance.

        # happy path for pool with and then without prior balance record
        for pool_name in ["test-pool-balance", "ROOT"]:
            test_pool = Pool.objects.get(name=pool_name)
            pId = test_pool.id
            data = {"force": "false"}
            r = self.client.post(
                "{}/{}/balance/status".format(self.BASE_URL, pId), data=data
            )
            self.assertTrue(status.is_success(r.status_code))
            # if HTTP_204_NO_CONTENT we have no content to assert anything on.
            if r.status_code is status.HTTP_204_NO_CONTENT:
                continue

            # We compare only our known values individually as the returned lastest
            # pool balance entry will also have start_time etc
            self.assertEqual(
                r.data["status"],
                self.default_balance_status["status"],
                msg="Failed status return. \n Got ({}) \nExpected ({})".format(
                    r.data["status"], self.default_balance_status["status"]
                ),
            )
            self.assertEqual(
                r.data["percent_done"],
                self.default_balance_status["percent_done"],
                msg="Failed percent_done return. \n Got ({}) \nExpected ({})".format(
                    r.data["percent_done"], self.default_balance_status["percent_done"]
                ),
            )

    def test_post_status_running_cli_balance(self):
        """
        Test POST to balance status command with:
        - no CLI balance but 2 existing (in fixture) balance records.
        - mocked CLI balance "running state" 6% done.
        - mocked CLI balance "running state" 6% done.
        - mocked CLI balance "running state" 50% done.
        - no CLI balance.
        Ensure expected results of a single new CLI entry created and then updated.
        Final status as finished.
        """
        loop_test_pool = Pool.objects.get(name="test-pool-balance")
        pId = loop_test_pool.id

        pb = PoolBalance.objects.filter(pool=pId).latest("start_time")
        last_pb_tid = pb.tid

        # We begin with no cli balance in effect, resulting in our last balance record
        # being returned, i.e. last in fixtures.
        balance_status = [{"status": "finished", "percent_done": 100}]  # No cli balance
        balance_status.append({"status": "running", "percent_done": 6})
        balance_status.append({"status": "running", "percent_done": 6})
        balance_status.append({"status": "running", "percent_done": 50})
        balance_status.append({"status": "finished", "percent_done": 100})
        # test-pool-balance as 2 prior PoolBalance records, above should give:
        balance_tasks_id = {
            "test-pool-balance": [pb.tid, None, None, None, None],
            # But ROOT has no prior balance record so:
            "ROOT": [None, None, None, None, None],
        }
        poolBalanceID = {
            "test-pool-balance": [2, 3, 3, 3, 3],
            "ROOT": [None, 4, 4, 4, 4],
        }
        poolBalanceMessage = [None]
        poolBalanceMessage.extend(
            ["Suspected cli balance detected. New entry created."] * 4
        )

        for pool_name in ["test-pool-balance", "ROOT"]:
            loop_test_pool = Pool.objects.get(name=pool_name)
            pId = loop_test_pool.id
            # Create a test data loop with auto generated index (0 indexed).
            for test_data_index, (bstatus, btid, pbid, pbmessage) in enumerate(
                zip(
                    balance_status,
                    balance_tasks_id[pool_name],
                    poolBalanceID[pool_name],
                    poolBalanceMessage,
                )
            ):
                self.mock_balance_status.return_value = bstatus
                r = self.client.post("{}/{}/balance/status".format(self.BASE_URL, pId))
                # Account for HTTP_204_NO_CONTENT: success but no prior balance record.
                self.assertTrue(status.is_success(r.status_code))
                # self.assertEqual(r.status_code, status.HTTP_200_OK, msg=r.data)

                e_msg = (
                    "failed recording cli status. \n Got ({}) \nExpected ({})."
                    "\nPool name {}, Test data index {}".format(
                        r.data, bstatus, pool_name, test_data_index
                    )
                )

                # if HTTP_204_NO_CONTENT we have no content to assert anything on.
                if r.status_code is status.HTTP_204_NO_CONTENT:
                    continue

                # We compare only our known values individually as the new pool balance
                # entry will also have start_time etc
                self.assertEqual(r.data["status"], bstatus["status"], msg=e_msg)
                self.assertEqual(
                    r.data["percent_done"], bstatus["percent_done"], msg=e_msg
                )
                # cli balance has no Huey task id as it was not run via Huey.
                self.assertEqual(
                    r.data["tid"],
                    btid,
                    msg="unexpected tid: Got {}, Expected {}."
                    "\nPool name {}, Test data index {}".format(
                        r.data["tid"], btid, pool_name, test_data_index
                    ),
                )
                # We should have a known id for PoolBalance entry.
                self.assertEqual(
                    r.data["id"],
                    pbid,
                    msg="Id of PoolBalance record incorrect. Got {} Expected {}."
                    "\nPool name {}, Test data index {}.".format(
                        r.data["id"], pbid, pool_name, test_data_index
                    ),
                )
                # Assert user visible 'message'
                self.assertEqual(
                    r.data["message"],
                    pbmessage,
                    msg="PoolBalance message issue. Got {}, expected {}."
                    "\nPool name {}, Test data index {}".format(
                        r.data["message"], pbmessage, pool_name, test_data_index
                    ),
                )

        # reset to default return value.
        self.mock_balance_status.return_value = self.default_balance_status
