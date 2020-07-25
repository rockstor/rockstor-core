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
from rest_util import api_error, api_call


class NFSExportConsole(BaseConsole):
    def __init__(self, prompt):
        BaseConsole.__init__(self)
        self.prompt = prompt + " NFS-Exports>"
        self.baseurl = "%sadv-nfs-exports" % BaseConsole.url

    @api_error
    def do_list(self, args):
        print(api_call(self.baseurl))

    @api_error
    def do_add(self, args):
        """
        Add advanced nfs export entries. aka edit /etc/exports file directly.

        add exports_line

        parameters:
        exports_line:    Intended line of /etc/exports.
                         eg: /exports/share1 example.com(rw,no_root_squash)
                         for multiple entries, use | as the separator.
                         eg: /exports/s1 example.com(rw) | /exports/s2 *(ro)
        """
        exports = []
        if args != "":
            exports = args.split("|")
        input_data = {
            "entries": exports,
        }
        print(
            api_call(
                self.baseurl,
                data=input_data,
                headers={"content-type": "application/json"},
                calltype="post",
            )
        )
