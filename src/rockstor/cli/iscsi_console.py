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
from share_iscsi_console import ShareIscsiConsole
from rest_util import api_call


class IscsiConsole(BaseConsole):
    def __init__(self, prompt):
        BaseConsole.__init__(self)
        self.prompt = prompt + " Iscsi>"
        self.url = BaseConsole.url + "sm/services/iscsi/"

    def do_status(self, args):
        iscsi_info = api_call(self.url)
        print(iscsi_info)

    def put_wrapper(self, args, command):
        input_data = {
            "command": command,
        }
        iscsi_info = api_call(self.url, data=input_data, calltype="put")
        print(iscsi_info)

    def do_start(self, args):
        return self.put_wrapper(args, "start")

    def do_stop(self, args):
        return self.put_wrapper(args, "stop")

    def do_share(self, args):
        input_share = args.split()
        if len(input_share) > 0:
            si_console = ShareIscsiConsole(input_share[0])
            if len(input_share) > 1:
                si_console.onecmd(" ".join(input_share[1:]))
            else:
                si_console.cmdloop()
