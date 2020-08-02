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


class SMConsole(BaseConsole):
    def __init__(self, prompt):
        BaseConsole.__init__(self)
        self.greeting = "Smart Manager"
        self.pprompt = prompt
        self.prompt = "%s %s>" % (self.pprompt, self.greeting)
        self.baseurl = BaseConsole.url + "sm/sprobes/"

    def do_data(self, args):
        if args is not None:
            tap_fields = args.split()
            url = "%s%s/%s/data?%s" % (
                self.baseurl,
                tap_fields[0],
                tap_fields[1],
                tap_fields[2],
            )
            stap_info = api_call(url)
            print(stap_info)
        else:
            return self.do_help(args)

    def do_data2(self, args):
        if args is not None:
            tap_fields = args.split()
            url = "%s%s?%s" % (self.baseurl, tap_fields[0], tap_fields[1])
            print(api_call(url))
        else:
            return self.do_help(args)

    def do_list(self, args):
        print(api_call(self.baseurl))

    def do_stop(self, args):
        if args is not None:
            tap_fields = args.split()
            url = "%s%s/%s/stop" % (self.baseurl, tap_fields[0], tap_fields[1])
            stap_info = api_call(url, data=None, calltype="post")
            print(stap_info)
        else:
            return self.do_help(args)

    def do_start(self, args):
        """
        start probe_name display_name
        """
        tap_fields = args.split()
        if len(tap_fields) > 0:
            tname = tap_fields[0]
            url = "%s%s" % (self.baseurl, tname)
            stap_info = api_call(
                url, data={"display_name": tap_fields[1],}, calltype="post"
            )
            print(stap_info)
        else:
            return self.do_help(args)
