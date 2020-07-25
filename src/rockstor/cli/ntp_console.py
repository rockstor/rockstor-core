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


class NTPConsole(BaseConsole):
    def __init__(self, prompt):
        BaseConsole.__init__(self)
        self.prompt = prompt + " NTP>"
        self.baseurl = "%ssm/services/ntpd" % BaseConsole.url

    def do_config(self, args):
        """
        config server_name
        """
        url = "%s/config" % self.baseurl
        fields = args.split()
        input_data = {
            "config": {"server": fields[0],},
        }
        headers = {"content-type": "application/json"}
        api_call(url, data=input_data, calltype="post", headers=headers)

    def do_status(self, args):
        ntp_info = api_call(self.baseurl)
        print(ntp_info)

    def do_start(self, args):
        return self.put_wrapper(args, "start")

    def do_stop(self, args):
        return self.put_wrapper(args, "stop")

    def put_wrapper(self, args, command):
        url = "%s/%s" % (self.baseurl, command)
        ntp_info = api_call(url, calltype="post")
        print(ntp_info)
