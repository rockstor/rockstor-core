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
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""


from base_console import BaseConsole
from share_nfs_console import ShareNFSConsole
from rest_util import api_call


class NFSConsole(BaseConsole):
    def __init__(self, prompt):
        BaseConsole.__init__(self)
        self.prompt = prompt + " NFS>"
        self.baseurl = "%ssm/services/nfs" % BaseConsole.url

    def do_status(self, args):
        nfs_info = api_call(self.baseurl)
        print(nfs_info)

    def do_start(self, args):
        return self.put_wrapper(args, "start")

    def do_stop(self, args):
        return self.put_wrapper(args, "stop")

    def put_wrapper(self, args, command):
        url = "%s/%s" % (self.baseurl, command)
        nfs_info = api_call(url, calltype="post")
        print(nfs_info)

    def do_shares(self, args):
        pass

    def do_share(self, args):
        input_share = args.split()
        if len(input_share) > 0:
            sn_console = ShareNFSConsole(input_share[0])
            if len(input_share) > 1:
                sn_console.onecmd(" ".join(input_share[1:]))
            else:
                sn_console.cmdloop()
