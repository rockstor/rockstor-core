"""
Copyright (c) 2012-2023 RockStor, Inc. <https://rockstor.com>
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
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
from huey.contrib.djhuey import HUEY
from rest_framework import status
from unittest.mock import patch
from storageadmin.tests.test_api import APITestMixin
from storageadmin.models import Pool, PoolBalance
from storageadmin.views.pool_balance import is_pending_balance_task
import time
from huey.exceptions import TaskException

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


class PoolBalanceTestsHuey(APITestMixin):
    fixtures = ["test_api.json", "test_pool_balance.json"]
    BASE_URL = "/api/pools"
    default_balance_status = {"status": "finished", "percent_done": 100}

    @classmethod
    def setUpClass(cls):
        super(PoolBalanceTestsHuey, cls).setUpClass()

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

        # Mock balance_status() - Wrapper for 'btrfs balance status pool_mount_point'.
        # For testing our response to PUT add command (adding disks and/or re-raid).
        cls.patch_balance_status = patch("fs.btrfs.balance_status")
        cls.mock_balance_status = cls.patch_balance_status.start()
        cls.mock_balance_status.return_value = cls.default_balance_status

    @classmethod
    def tearDownClass(cls):
        super(PoolBalanceTestsHuey, cls).tearDownClass()

    def test_post_valid_balance_follow_through(self):
        """
        As our Huey run balance tasks rely on Huey events to recored end time etc,
        and we check during updates for pending or ongoing Huey tasks, this test
        needs a running Huey server. A Running Rockstor instance provides for this.
        """

        test_pool = Pool.objects.get(name="test-pool-balance")  # has balance record
        pId = test_pool.id

        # Request a balance via POST to pId/balance
        data = {"force": "false"}
        r = self.client.post("{}/{}/balance".format(self.BASE_URL, pId), data=data)
        self.assertEqual(r.status_code, status.HTTP_200_OK, msg=r.data)
        # check, via return, that we have model default/initial creation values.
        # Status as started
        self.assertEqual(
            r.data["status"],
            "started",
            msg="Failed status return.\nGot ({}) \nExpected ('started')".format(
                r.data["status"]
            ),
        )
        # Percent done as 0 as we have just initialized our PoolBalance instance.
        self.assertEqual(
            r.data["percent_done"],
            0,
            msg="Failed percent_done return.\nGot ({}).\nExpected (0)".format(
                r.data["status"]
            ),
        )
        # Huey tid is NOT None as that would be a cli initiated PoolBalance indicator.
        self.assertIsNotNone(
            r.data["tid"], msg="Failed tid check.\n Got ({})\nExpected ('Not None')"
        )
        huey_task_id = r.data["tid"]
        # Our PoolBalance end time defaults to None:
        # We haven't had Huey finish our balance task yet.
        self.assertIsNone(
            r.data["end_time"],
            msg="Failed end_time None check.\n Got ({})\nExpected ('None')",
        )
        # We mock balance_pool_cmd, run by Huey, to be a shell null-op: "true".
        # So it should complete successfully once our task has passed from pending/cued
        # to having been executed.
        huey_handle = HUEY
        # huey_handle.immediate = True
        self.assertTrue(
            is_pending_balance_task(huey_handle, huey_task_id),
            msg="Expected pending Huey task id ({}) not found".format(huey_task_id),
        )
        # TODO test case for huey task set akin to what we already have in the already functional
        #  cli counterparts within test_pool_balance.py test_post_status_running_cli_balance()
        #  see below for hints.


        # huey_handle.immediate = True
        # # Await, with time-out, our huey task's transition from pending to execution:
        # # and then assert that we have a non 'None' end time.
        # # N.B. use of Huey immediate mode when testing:
        # # https://huey.readthedocs.io/en/latest/api.html#Huey.immediate
        # # However this could introduce, or cover up, race conditions.
        # time_out = 6  # Seconds to wait for Huey to begin execution of a 'pending' task.
        # while time_out:
        #     time.sleep(1)
        #     print(time_out)
        #     time_out -= 1
        #     if not is_pending_balance_task(huey_handle, huey_task_id):
        #         break
        # # Wait for huey task null-op execution (0.007s to 0.009s)
        # time.sleep(1)
        # # Check that the associated PoolBalance db record has been updated appropriately
        # # with an end time.
        # # N.B. We don't make a status api call as this, in turn, does it's own update.
        # # We are checking that the Huey task_completed() event has update db end_time.
        # #
        # # the following PoolBalance has already been proven to exist in a prior step.
        # Huey_PoolBalance_record = PoolBalance.objects.filter(tid=huey_task_id).latest()
        # print(Huey_PoolBalance_record.end_time)
        # self.assertIsNotNone(
        #     Huey_PoolBalance_record.end_time,
        #     msg="Failed end_time NOT None check. Got {}, Expected {}.".format(
        #         Huey_PoolBalance_record.end_time, "NOT None"
        #     ),
        # )

        # post a pool status request:
        # r = self.client.post("{}/{}/balance/status".format(self.BASE_URL, pId))
        # # test for matching huey task id
        # self.assertEqual(r.data["tid"], huey_task_id, msg="Failed to match Huey tid")
        # # test for completed end_time: see tasks.py
        # self.assertIsNotNone(
        #     r.data["end_time"],
        #     msg="Failed non None end_time. Got {}, Expected {}.".format(
        #         r.data["end_time"], "not None"
        #     ),
        # )

        # time_out = 3
        # task_result = None
        # while time_out and task_result:
        #     time.sleep(1)
        #     print("awaiting huey_task completion {}".format(time_out))
        #     time_out -= 1
        #     try:
        #         # we must preserve our huey task result for our tested code to consume
        #         task_result = huey_handle.result(huey_task_id, preserve=True)
        #         print(task_result)
        #     except TaskException as e:
        #         print(
        #             "task exception thrown during test read {()}".format(
        #                 e.metadata.get("traceback", "missing 'traceback' key")
        #             )
        #         )
        #         break
        # print(PoolBalance.objects.filter(tid=huey_task_id).latest().end_time)
        # self.assertIsNotNone(
        #     PoolBalance.objects.filter(tid=huey_task_id).latest().end_time,
        #     msg="Failed end_time Not None check.",
        # )



