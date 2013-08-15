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


from base_console import BaseConsole
from rest_util import (api_call, print_export_info, print_share_info)


class SnapshotConsole(BaseConsole):

    def __init__(self, prompt, share):
        BaseConsole.__init__(self)
        self.share = share
        self.prompt = prompt + ' snapshots>'
        self.url = ('%sshares/%s/snapshots' % (BaseConsole.url, self.share))

    def do_list(self, args):
        """
        List all snapshots
        """
        snap_info = api_call(self.url)
        print snap_info

    def do_add(self, args):
        """
        Add a new snapshot.

        add <snap_name>
        """
        url = ('%s/%s' % (self.url, args))
        snap_info = api_call(url, data=None, calltype='post')
        print snap_info

    def do_delete(self, args):
        """
        Delete a snapshot.

        delete <snap_name>
        """
        url = ('%s/%s' % (self.url, args))
        snap_info = api_call(url, data=None, calltype='delete')
        print snap_info

    def do_rollback(self, args):
        """
        Rollback a snapshot.

        rollback <snap_name>
        """
        url = ('%s/%s/rollback' % (self.url, args))
        snap_info = api_call(url, data=None, calltype='post')
        print snap_info

