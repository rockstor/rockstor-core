"""
Copyright (c) 2012-2020 RockStor, Inc. <http://rockstor.com>
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

from base_console import BaseConsole
from rest_util import api_call, print_disk_info


class SetupConsole(BaseConsole):
    def __init__(self, prompt):
        BaseConsole.__init__(self)
        self.prompt = prompt + " setup>"

    def do_disks(self, args):
        """
        Discover and setup disks.
        """
        url = BaseConsole.url + "tools/sysdisks/"
        result = api_call(url, calltype="post")
        print("Setup is complete")
        print_disk_info(result)
