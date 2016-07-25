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


import unittest
from fs.btrfs import add_pool, pool_raid
import mock
from mock import patch


class Pool(object):

    def __init__(self, raid, name):
        self.raid = raid
        self.name = name


class BTRFSTests(unittest.TestCase):

    def setUp(self):
        self.patch_run_command = patch('fs.btrfs.run_command')
        self.mock_run_command = self.patch_run_command.start()

    def tearDown(self):
        patch.stopall()

    #sample test
    def test_add_pool_mkfs_fail(self):
        pool = Pool(raid='raid0', name='mypool')
        disks = ('sdb', 'sdc')
        self.mock_run_command.side_effect = Exception('mkfs error')
        self.assertEqual(add_pool(pool, disks), 1)

    def test_get_pool_raid_levels(self):
        """
        Presents the raid identification function with example data and compares
        it's return dict to that expected for the given input.
        :return: 'ok' if all is as expected or a message indicating which raid
        level was incorrectly identified given the test data.
        """
        # setup fake mount point
        mount_point = '/mnt2/fake-pool'
        cmd_rc = 0
        cmd_e = ['']
        # setup example btrfs fi df mount_point outputs for given inputs.
        # Outputs are simple lists of whole lines output from btrfs fi df
        # expected return is a dict of extracted info from above btrfs command.
        single_fi_df = ['Data, single: total=8.00MiB, used=64.00KiB', 'System, single: total=4.00MiB, used=16.00KiB', 'Metadata, single: total=216.00MiB, used=128.00KiB', 'GlobalReserve, single: total=16.00MiB, used=0.00B', '']
        single_return = {'data': 'single', 'system': 'single', 'globalreserve': 'single', 'metadata': 'single'}
        raid0_fi_df = ['Data, RAID0: total=512.00MiB, used=256.00KiB', 'System, RAID0: total=16.00MiB, used=16.00KiB', 'Metadata, RAID0: total=512.00MiB, used=128.00KiB', 'GlobalReserve, single: total=16.00MiB, used=0.00B', '']
        raid0_return = {'data': 'raid0', 'system': 'raid0', 'globalreserve': 'single', 'metadata': 'raid0'}
        raid1_fi_df = ['Data, RAID1: total=512.00MiB, used=192.00KiB', 'System, RAID1: total=32.00MiB, used=16.00KiB', 'Metadata, RAID1: total=256.00MiB, used=128.00KiB', 'GlobalReserve, single: total=16.00MiB, used=0.00B', '']
        raid1_return = {'data': 'raid1', 'system': 'raid1', 'globalreserve': 'single', 'metadata': 'raid1'}
        # Thanks to @grebnek in forum and GitHub for spotting this:
        # https://btrfs.wiki.kernel.org/index.php/FAQ#Why_do_I_have_.22single.22_chunks_in_my_RAID_filesystem.3F
        # when converting from single to another raid level it is normal for
        # a few chunks to remain in single until the next balance operation.
        raid1_fi_df_some_single_chunks = ['Data, RAID1: total=416.00MiB, used=128.00KiB', 'Data, single: total=416.00MiB, used=0.00B', 'System, RAID1: total=32.00MiB, used=16.00KiB', 'Metadata, RAID1: total=512.00MiB, used=128.00KiB', 'GlobalReserve, single: total=16.00MiB, used=0.00B', '']
        # for a time we incorrectly parsed the last btrfs fi df mount_point as the following
        # raid1_some_single_chunks_return = {'data': 'single', 'system': 'raid1', 'globalreserve': 'single', 'metadata': 'raid1'}
        # but the expected result should be the same as "raid1_return" above. ie data raid1 not single.
        raid10_fi_df = ['Data, RAID10: total=419.75MiB, used=128.00KiB', 'System, RAID10: total=16.00MiB, used=16.00KiB', 'Metadata, RAID10: total=419.75MiB, used=128.00KiB', 'GlobalReserve, single: total=16.00MiB, used=0.00B', '']
        raid10_return = {'data': 'raid10', 'system': 'raid10', 'globalreserve': 'single', 'metadata': 'raid10'}
        raid5_fi_df = ['Data, RAID5: total=215.00MiB, used=128.00KiB', 'System, RAID5: total=8.00MiB, used=16.00KiB', 'Metadata, RAID5: total=215.00MiB, used=128.00KiB', 'GlobalReserve, single: total=16.00MiB, used=0.00B', '']
        raid5_return = {'data': 'raid5', 'system': 'raid5', 'globalreserve': 'single', 'metadata': 'raid5'}
        raid6_fi_df = ['Data, RAID6: total=211.62MiB, used=128.00KiB', 'System, RAID6: total=8.00MiB, used=16.00KiB', 'Metadata, RAID6: total=211.62MiB, used=128.00KiB', 'GlobalReserve, single: total=16.00MiB, used=0.00B', '']
        raid6_return = {'data': 'raid6', 'system': 'raid6', 'globalreserve': 'single', 'metadata': 'raid6'}
        # list used to report what raid level is currently under test.
        raid_levels_tested = ['single', 'raid0', 'raid1', 'raid10', 'raid5',
                              'raid6']
        self.mock_run_command.return_value = (single_fi_df, cmd_e, cmd_rc)
        self.assertEqual(pool_raid(mount_point), single_return)
