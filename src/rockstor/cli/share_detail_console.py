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
from share_nfs_console import ShareNFSConsole
from share_smb_console import ShareSMBConsole
from share_iscsi_console import ShareIscsiConsole
from snapshot_console import SnapshotConsole
from rest_util import api_error


class ShareDetailConsole(BaseConsole):
    def __init__(self, greeting, share):
        BaseConsole.__init__(self)
        self.share = share
        self.greeting = greeting + " " + self.share
        self.prompt = self.greeting + "> "
        self.url = "%sshares/%s/" % (BaseConsole.url, self.share)

    @api_error
    def do_nfs(self, args):
        """
        nfs operations on the share
        """
        sn_console = ShareNFSConsole(self.greeting, self.share)
        sn_console.cmdloop()

    @api_error
    def do_smb(self, args):
        """
        smb operations on the share
        """
        ss_console = ShareSMBConsole(self.greeting, self.share)
        ss_console.cmdloop()

    @api_error
    def do_iscsi(self, args):
        """
        iscsi operations on the share
        """
        i_console = ShareIscsiConsole(self.greeting, self.share)
        i_console.cmdloop()

    @api_error
    def do_snapshot(self, args):
        """
        snapshot operations on the share
        """
        input_snap = args.split()
        snap_console = SnapshotConsole(self.greeting, self.share)
        if len(input_snap) > 0:
            return snap_console.onecmd(" ".join(input_snap))
        snap_console.cmdloop()
