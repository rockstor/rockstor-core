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


class UsersConsole(BaseConsole):
    def __init__(self, prompt):
        BaseConsole.__init__(self)
        self.greeting = "Users"
        self.pprompt = prompt
        self.prompt = "%s %s>" % (self.pprompt, self.greeting)
        self.base_url = "%s/users/" % BaseConsole.url

    def do_list(self, args):
        url = self.base_url
        if len(args) > 0:
            url = "%s%s" % (self.base_url, args.split()[0])
        user_info = api_call(url)
        print(user_info)

    def do_add(self, args):
        if len(args) > 0:
            username, pw, utype = args.split()
            data = {
                "username": username,
                "password": pw,
                "utype": utype,
            }
            user_info = api_call(self.base_url, data=data, calltype="post")
            print(user_info)
        else:
            self.do_help(args)

    def do_passwd(self, args):
        if len(args) > 0:
            username, pw = args.split()
            data = {"password": pw}
            url = "%s%s/" % (self.base_url, username)
            user_info = api_call(url, data=data, calltype="put")
            print(user_info)
        else:
            self.do_help(args)

    def do_delete(self, args):
        if len(args) > 0:
            username = args.split()[0]
            url = "%s%s" % (self.base_url, username)
            user_info = api_call(url, calltype="delete")
            print(user_info)
        else:
            self.do_help(args)
