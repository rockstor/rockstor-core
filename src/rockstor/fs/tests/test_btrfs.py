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
from fs.btrfs import add_pool
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
