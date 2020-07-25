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
from rest_util import api_call


class ShareIscsiConsole(BaseConsole):
    def __init__(self, prompt, share):
        BaseConsole.__init__(self)
        self.share = share
        self.prompt = prompt + " iscsi>"
        self.url = "%sshares/%s/iscsi/" % (BaseConsole.url, self.share)

    def do_enable(self, args):
        """
        enable iscsi for the given share

        enable -n foosczi -i 2
        """
        arg_fields = args.split()
        input_data = {}
        for f in arg_fields:
            if f[0:2] == "-n":
                input_data["tname"] = f[2:]
            elif f[0:2] == "-i":
                input_data["tid"] = f[2:]
            else:
                return self.do_help(args)
        if len(input_data) != 2:
            return self.do_help(args)
        iscsi_info = api_call(self.url, data=input_data, calltype="post")
        print(iscsi_info)

    def do_disable(self, args):
        iscsi_info = api_call(self.url, data=None, calltype="delete")
        print(iscsi_info)

    def do_list(self, args):
        iscsi_info = api_call(self.url, data=None)
        print(iscsi_info)
