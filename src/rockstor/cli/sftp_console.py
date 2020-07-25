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
from rest_util import (
    api_error,
    api_call,
)


class SFTPConsole(BaseConsole):
    def __init__(self, prompt):
        BaseConsole.__init__(self)
        self.prompt = prompt + " SFTP>"
        self.url = BaseConsole.url + "sm/services/sftp/"

    def do_status(self, args):
        sftp_info = api_call(self.url)
        print(sftp_info)

    def put_wrapper(self, args, command):
        input_data = {
            "command": command,
        }
        sftp_info = api_call(self.url, data=input_data, calltype="put")
        print(sftp_info)

    def do_start(self, args):
        return self.put_wrapper(args, "start")

    def do_stop(self, args):
        return self.put_wrapper(args, "stop")

    @api_error
    def do_add_sftp(self, args):
        """
        enable_sftp share1,share2,... <rw|ro>
        """
        fields = args.split()
        shares = fields[0].split(",")
        print(shares)
        input_data = {
            "shares": shares,
            "read_only": True,
        }
        url = BaseConsole.url + "sftp"
        headers = {"content-type": "application/json"}
        sftp_info = api_call(url, data=input_data, headers=headers, calltype="post")
        print(sftp_info)

    def do_list_sftp(self, args):
        """
        list_sftp
        """
        print(api_call(BaseConsole.url + "sftp"))

    def do_delete_sftp(self, args):
        """
        delete_sftp id
        """
        url = "%ssftp/%s" % (BaseConsole.url, args)
        print(api_call(url, calltype="delete"))
