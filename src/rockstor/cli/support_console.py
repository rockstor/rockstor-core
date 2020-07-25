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


class SupportConsole(BaseConsole):
    def __init__(self, prompt):
        BaseConsole.__init__(self)
        self.greeting = "Support"
        self.pprompt = prompt
        self.prompt = "%s %s>" % (self.pprompt, self.greeting)
        self.baseurl = BaseConsole.url + "support/"

    def do_list(self, args):
        """
        List support cases
        """
        url = self.baseurl
        if args is not None:
            case_fields = args.split()
            if len(case_fields) > 0:
                url = "%s%s/" % (url, case_fields[0])
        case_info = api_call(url)
        print(case_info)

    def do_add(self, args):
        """
        Add a support case

        add -nnotes
        """
        case_fields = args.split()
        if len(case_fields) < 1:
            return self.do_help(args)

        input_data = {
            "type": "manual",
        }
        for f in case_fields:
            if f[0:2] == "-n":
                input_data["notes"] = f[2:]
        if len(input_data) < 2:
            return self.do_help(args)

        case_info = api_call(self.baseurl, data=input_data, calltype="put")
        print(case_info)

    def do_update(self, args):
        """
        Update the status of a support case

        update <case_id> <resolved|submitted>
        """
        case_fields = args.split()
        if len(case_fields) < 2:
            return self.do_help(args)

        input_data = {"status": case_fields[1]}
        url = "%s%s/" % (self.baseurl, case_fields[0])
        case_info = api_call(url, data=input_data, calltype="put")
        print(case_info)
