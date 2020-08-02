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
from pool_detail_console import PoolDetailConsole
from rest_util import (
    api_error,
    api_call,
    print_pools_info,
    print_pool_info,
    print_scrub_status,
)


class PoolsConsole(BaseConsole):
    def __init__(self, prompt):
        BaseConsole.__init__(self)
        self.prompt = prompt + " Pools> "
        self.url = "%spools" % BaseConsole.url

    @api_error
    def do_list(self, args):
        url = self.url + "?format=json"
        if args:
            # print info for a single pool
            url = "%s/%s" % (self.url, args)
            pool_info = api_call(url)
            print_pool_info(pool_info, True)
        else:
            pools_info = api_call(url)
            print_pools_info(pools_info)

    def help_list(self):
        snps = "Display details of the appliance's pools"
        params = {
            "<pool_name>": ("(optional)Print details of the given pool only"),
        }
        self.print_help(snps, "list", args=("<pool_name>",), params=params)

    @api_error
    def do_add(self, args):
        arg_fields = args.split()
        if len(arg_fields) < 3:
            error = "3 arguments expected. %d given" % len(arg_fields)
            return self.help_wrapper(error, "add")

        input_data = {
            "pname": arg_fields[0],
            "disks": arg_fields[1],
            "raid_level": arg_fields[2],
        }
        url = self.url
        pool_info = api_call(url, data=input_data, calltype="post")
        print_pool_info(pool_info)

    def help_add(self):
        args = (
            "pool_name",
            "disk_list",
            "raid_type",
        )
        params = {
            "pool_name": "Intended name of the pool",
            "disk_list": (
                "A list of comma-separated(no whitespace) "
                "disks. For example: sdb,sdc"
            ),
            "raid_type": ("One of the following: single, raid0, raid1 and raid10"),
        }
        examples = {
            (
                "Create a raid0 pool with two disks(sdb and sdc) called pool0"
            ): "pool0 sdb,sdc raid0",
        }
        self.print_help("Create a new pool.", "add", args, params, examples)

    @api_error
    def do_delete(self, args):
        if len(args) == 0:
            return self.help_wrapper("missing pool_name", "delete")
        url = "%s/%s" % (self.url, args)
        print("Deleting pool %s" % args[0])
        api_call(url, calltype="delete")
        print("Pool %s deleted" % args[0])

    def help_delete(self):
        params = {
            "pool_name": "Name of the pool to delete",
        }
        examples = {
            "Delete a pool named pool0": "pool0",
        }
        self.print_help(
            "Delete a pool",
            "delete",
            args=("pool_name",),
            params=params,
            examples=examples,
        )

    @api_error
    def do_console(self, args):
        pd_console = PoolDetailConsole("foo")
        input_pool = args.split()
        if len(input_pool) > 0:
            pd_console.set_prompt(input_pool[0])
            pd_console.cmdloop()
        else:
            pd_console.onecmd(args)

    def help_console(self):
        snps = "Subconsole of a single pool"
        args = ("pool_name",)
        params = {
            "pool_name": "Name of the pool",
        }
        examples = {
            "Go to the console of a pool called mypool": "mypool",
        }
        self.print_help(snps, "console", args, params, examples)

    @api_error
    def do_scrub(self, args):
        if len(args) == 0:
            return self.help_wrapper("missing pool_name", "scrub")
        url = "%s/%s/scrub" % (self.url, args)
        scrub_info = api_call(url, calltype="post")
        print(scrub_info)

    def help_scrub(self):
        params = {
            "pool_name": "Name of the pool to scrub",
        }
        examples = {
            "Scrub a pool called mypool": "mypool",
        }
        self.print_help("Scrub a pool", "scrub", ("pool_name",), params, examples)

    @api_error
    def do_scrubstatus(self, args):
        if len(args) == 0:
            return self.help_wrapper("missing pool_name", "scrub_status")
        url = "%s/%s/scrub/status" % (self.url, args)
        scrub_info = api_call(url, calltype="post")
        print_scrub_status(args, scrub_info)

    def help_scrubstatus(self):
        snps = "Print scrub status of a pool"
        params = {
            "pool_name": "Name of the pool",
        }
        examples = {
            "Print scrub status of a pool mypool": "mypool",
        }
        self.print_help(
            snps, "scrubstatus", args=("pool_name",), params=params, examples=examples
        )
