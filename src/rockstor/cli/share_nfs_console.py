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
from rest_util import api_call, print_export_info


class ShareNFSConsole(BaseConsole):
    def __init__(self, greeting, share):
        BaseConsole.__init__(self)
        self.share = share
        self.greeting = greeting + " nfs"
        self.prompt = self.greeting + "> "
        self.url = "%sshares/%s/nfs" % (BaseConsole.url, self.share)

    def do_exports(self, args):
        """
        List all exports
        """
        export_info = api_call(self.url)
        print_export_info(export_info)

    def do_add_export(self, args):
        arg_fields = args.split()
        input_data = {}
        for f in arg_fields:
            if f[0:2] == "-c":
                input_data["host_str"] = f[2:]
            elif f[0:2] == "-m":
                input_data["mod_choice"] = f[2:]
            elif f[0:2] == "-s":
                input_data["sync_choice"] = f[2:]
            else:
                return self.do_help(args)
        if len(input_data) != 3:
            return self.do_help(args)
        export_info = api_call(self.url, data=input_data, calltype="post")
        print_export_info(export_info)

    def help_add_export(self):
        snps = "Add a new nfs export"
        args = (
            "-c host_str",
            "-m mod_choice",
            "-s sync_choice",
        )
        params = {
            "host_str": "Host string",
            "mod_choice": (
                "Specified whether the share is writeable "
                "or readonly. Can be either 'rw' or 'ro'"
            ),
            "sync_choice": ("Specifies sync or async, can be either 'sync' or 'async'"),
        }
        self.print_help(snps, "add_export", args=args, params=params)

    def do_disable_export(self, args):
        """
        To disable an export

        disable_export export_id
        """
        return self._toggle_export(args, "nfs-disable")

    def do_enable_export(self, args):
        """
        To enable a (previously disabled) export

        enable_export export_id
        """
        return self._toggle_export(args, "nfs-enable")

    def do_delete_export(self, args):
        """
        To delete an export

        delete_export export_id
        """
        try:
            export_id = int(args.split()[0])
        except Exception:
            self.do_help(args)
        url = "%s/%d/" % (self.url, export_id)
        export_info = api_call(url, data=None, calltype="delete")
        print(export_info)

    def _toggle_export(self, args, switch):
        try:
            export_id = int(args.split()[0])
        except Exception:
            self.do_help(args)
        url = "%sshares/%s/%s/" % (BaseConsole.url, self.share, switch)
        input_data = {
            "id": export_id,
        }
        export_info = api_call(url, data=input_data, calltype="put")
        print_export_info(export_info)
