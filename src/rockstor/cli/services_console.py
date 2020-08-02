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
from nfs_console import NFSConsole
from smb_console import SMBConsole
from sftp_console import SFTPConsole
from rest_util import api_call
from iscsi_console import IscsiConsole
from nis_console import NISConsole
from ntp_console import NTPConsole


class ServicesConsole(BaseConsole):
    def __init__(self, prompt):
        BaseConsole.__init__(self)
        self.greeting = "Services"
        self.pprompt = prompt
        self.prompt = "%s %s>" % (self.pprompt, self.greeting)

    def do_list(self, args):
        url = BaseConsole.url + "sm/services/"
        service_info = api_call(url)
        print(service_info)

    def do_nfs(self, args):
        return self.sub_service(args, "nfs")

    def do_nis(self, args):
        return self.sub_service(args, "nis")

    def do_nginx(self, args):
        pass

    def do_sftp(self, args):
        return self.sub_service(args, "sftp")

    def do_samba(self, args):
        return self.sub_service(args, "samba")

    def do_iscsi(self, args):
        return self.sub_service(args, "iscsi")

    def do_ntp(self, args):
        return self.sub_service(args, "ntp")

    def sub_service(self, args, name):
        greeting = self.pprompt + " " + self.greeting
        sub_console = None
        if name == "samba":
            sub_console = SMBConsole(greeting)
        elif name == "nfs":
            sub_console = NFSConsole(greeting)
        elif name == "sftp":
            sub_console = SFTPConsole(greeting)
        elif name == "iscsi":
            sub_console = IscsiConsole(greeting)
        elif name == "nis":
            sub_console = NISConsole(greeting)
        elif name == "ntp":
            sub_console = NTPConsole(greeting)
        else:
            return self.do_help(args)
        if len(args) == 0:
            sub_console.cmdloop()
