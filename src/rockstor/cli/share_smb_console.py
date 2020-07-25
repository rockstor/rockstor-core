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


class ShareSMBConsole(BaseConsole):
    def __init__(self, prompt, share):
        BaseConsole.__init__(self)
        self.prompt = prompt + " Samba>"
        self.share = share
        self.url = "%sshares/%s/samba/" % (BaseConsole.url, self.share)

    def do_enable(self, args):
        """
        Make the share available via smb. all flags are optional.

        enable -c comment [-b <yes|no> -g <yes|no> -r <yes|no> -m 0755]
        """
        arg_fields = args.split()
        input_data = {}
        for f in arg_fields:
            if f[0:2] == "-c":
                input_data["comment"] = f[2:]
            elif f[0:2] == "-b":
                input_data["browsable"] = f[2:]
            elif f[0:2] == "-g":
                input_data["guest_ok"] = f[2:]
            elif f[0:2] == "-r":
                input_data["read_only"] = f[2:]
            elif f[0:2] == "-m":
                input_data["create_mask"] = f[2:]
            else:
                return self.do_help(args)
        if len(input_data) == 0:
            return self.do_help(args)
        samba_info = api_call(self.url, data=input_data, calltype="post")
        print(samba_info)

    def do_disable(self, args):
        """
        disable smb for the share
        """
        samba_info = api_call(self.url, data=None, calltype="delete")
        print(samba_info)

    def do_list(self, args):
        """
        show smb properties for the share
        """
        samba_info = api_call(self.url, data=None)
        print(samba_info)
