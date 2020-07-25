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


class APIKeyConsole(BaseConsole):
    def __init__(self, prompt):
        BaseConsole.__init__(self)
        self.prompt = prompt + " APIKey> "
        self.baseurl = "%soauth_app" % BaseConsole.url

    @api_error
    def do_list(self, args):
        url = self.baseurl
        if args:
            url = "%s/%s" % (url, args)
        print(api_call(url))

    def help_list(self):
        snps = "Print details of one or all disks in the appliance"
        args = ("<disk_name>",)
        params = {
            "<disk_name>": ("(optional)Print details of the given disk only"),
        }
        examples = {
            "Print details of all disks in the system": "",
            "Print details of the disk named sdd": "sdd",
        }
        self.print_help(snps, "list", args, params, examples)

    @api_error
    def do_add(self, args):
        arg_fields = args.split()
        input_data = {
            "name": arg_fields[0],
            "username": arg_fields[1],
        }
        print(api_call(self.baseurl, data=input_data, calltype="post"))

    @api_error
    def do_delete(self, args):
        print(api_call(self.baseurl, data={"name": args,}, calltype="delete"))
