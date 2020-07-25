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
from share_detail_console import ShareDetailConsole
from rest_util import api_call, print_shares_info, print_share_info, api_error


class SharesConsole(BaseConsole):
    def __init__(self, greeting):
        BaseConsole.__init__(self)
        self.greeting = greeting + " Shares"
        self.prompt = self.greeting + "> "
        self.url = "%sshares" % BaseConsole.url

    @api_error
    def do_list(self, args):
        url = self.url
        if args:
            url = "%s/%s" % (self.url, args)
        shares_info = api_call(url)
        print_shares_info(shares_info)

    def help_list(self):
        snps = "Display details of shares on the appliance"
        args = ("<share_name>",)
        params = {
            "<share_name>": "(Optional)Name of a share",
        }
        examples = {
            "Display details of all shares": "",
            "Display details of a share called myshare": "myshare",
        }
        self.print_help(snps, "list", args, params, examples)

    @api_error
    def do_add(self, args):
        arg_fields = args.split()
        if len(arg_fields) < 3:
            error = "3 arguments expected. %d given" % len(arg_fields)
            return self.help_wrapper(error, "add")

        multiplier = 1024
        num = None
        try:
            num = int(arg_fields[2])
        except:
            if len(arg_fields[2]) > 2:
                try:
                    num = int(arg_fields[2][:-2])
                except:
                    error = "Invalid size parameter: %s" % arg_fields[2]
                    return self.help_wrapper(error, "add")
                suffix = arg_fields[2][-2:].lower()
                if suffix == "mb":
                    multiplier = multiplier ** 1
                elif suffix == "gb":
                    multiplier = multiplier ** 2
                elif suffix == "tb":
                    multiplier = multiplier ** 3
                elif suffix == "pb":
                    multiplier = multiplier ** 4
                else:
                    error = (
                        "Invalid size suffix: %s. must be one of "
                        "MB, GB, TB or PB" % suffix
                    )
                    return self.help_wrapper(error, "add")
            else:
                error = "Invalid size parameter: %s" % arg_fields[2]
                return self.help_wrapper(error, "add")
        size = num * multiplier
        input_data = {
            "sname": arg_fields[0],
            "pool": arg_fields[1],
            "size": size,
        }
        share_info = api_call(self.url, data=input_data, calltype="post")
        print_share_info(share_info)

    def help_add(self):
        args = (
            "share_name",
            "pool_name",
            "size",
        )
        params = {
            "share_name": "Intended name of the share",
            "pool_name": ("Pool in which to create the share. It must already exist"),
            "size": (
                "Intended size of the share. An integer with "
                "optional suffix(MB, GB, TB, PB). When no suffix "
                "is provided, MB is presumed"
            ),
        }
        examples = {
            "Create a 20GB share in a pool called pool": "share1234 pool0 20GB",
            "Create a 100MB share in a pool called mypool": "share100 mypool 100",
        }
        self.print_help(
            "Create a new share", "add", args=args, params=params, examples=examples
        )

    @api_error
    def do_resize(self, args):
        try:
            fields = args.split()
            sname = fields[0]
            new_size = int(fields[1])
        except:
            return self.do_help(args)
        input_data = {
            "size": new_size,
        }
        url = "%s/%s" % (self.url, sname)
        share_info = api_call(url, data=input_data, calltype="put")
        print_share_info(share_info)

    def help_resize(self):
        args = (
            "share_name",
            "new_size",
        )
        params = {
            "share_name": "Name of the share to resize",
            "new_size": "Desired new size of the share",
        }
        examples = {
            "Resize a share called myshare to 100GB": "myshare 100GB",
        }
        self.print_help(
            "Resize a share", "resize", args=args, params=params, examples=examples
        )

    @api_error
    def do_clone(self, args):
        fields = args.split()
        input_data = {
            "name": fields[1],
        }
        url = "%s/%s/clone" % (self.url, fields[0])
        print(api_call(url, data=input_data, calltype="post"))

    def help_clone(self):
        args = (
            "share_name",
            "clone_name",
        )
        self.print_help("Clone a share", "clone", args=args)

    @api_error
    def do_rollback(self, args):
        """
        Rollback a share to the state of one of it's snapshots.

        rollback <share_name> <snap_name>
        """
        fields = args.split()
        input_data = {
            "name": fields[1],
        }
        url = "%s/%s/rollback" % (self.url, fields[0])
        print(api_call(url, data=input_data, calltype="post"))

    @api_error
    def do_change_op(self, args):
        """
        To change ownership and permissions

        change_op share_name owner group perms
        """
        fields = args.split()
        input_data = {
            "owner": fields[1],
            "group": fields[2],
            "perms": fields[3],
        }
        url = "%s%s/acl" % (self.url, fields[0])
        share_info = api_call(url, data=input_data, calltype="post")
        print_share_info(share_info)

    def do_delete(self, args):
        """
        Delete a share
        """
        pass

    def do_disable(self, args):
        """
        Disable a share. Mark of deletion, but don't quite delete.
        """
        pass

    def do_enable(self, args):
        """
        Enable a previously disabled share
        """
        pass

    @api_error
    def do_share(self, args):
        """
        To go to a share console: share share_name
        """
        input_share = args.split()
        if len(input_share) > 0:
            sd_console = ShareDetailConsole(self.greeting, input_share[0])
            if len(input_share) > 1:
                return sd_console.onecmd(" ".join(input_share[1:]))
            return sd_console.cmdloop()
