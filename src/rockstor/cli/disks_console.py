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
from rest_util import api_error, api_call, print_disks_info, print_disk_info


class DisksConsole(BaseConsole):
    def __init__(self, prompt):
        BaseConsole.__init__(self)
        self.prompt = prompt + " Disks> "
        self.baseurl = "%sdisks" % BaseConsole.url

    @api_error
    def do_list(self, args):
        url = self.baseurl
        if args:
            # print info for a single disk
            url = "%s/%s" % (url, args)
            disk_info = api_call(url)
            print_disk_info(disk_info, True)
        else:
            # print info for all disks
            disks_info = api_call(url)
            print_disks_info(disks_info)

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
    def do_scan(self, args):
        url = "%s/scan" % self.baseurl
        api_call(url, data=None, calltype="post")
        self.do_list(None)

    def help_scan(self):
        snps = "Scan the system for new disks"
        examples = {
            snps: "",
        }
        self.print_help(snps, "scan", examples=examples)

    @api_error
    def do_delete(self, args):
        url = "%s/%s" % (self.baseurl, args)
        api_call(url, calltype="delete")
        print_disks_info(api_call(self.baseurl))

    def help_delete(self):
        snps = "Delete an offlined disk"
        args = ("disk_name",)
        params = {
            "disk_name": (
                "Name of the disk to be deleted. It must already be offlined"
            ),
        }
        self.print_help(snps, "delete", args=args, params=params)

    @api_error
    def do_wipe(self, args):
        url = "%s/%s/wipe" % (self.baseurl, args)
        api_call(url, calltype="post")
        print_disks_info(api_call(self.baseurl))

    def help_wipe(self):
        snps = "Wipe the partition table of a disk"
        params = {
            "disk_name": "Name of the disk to be wiped of it's data",
        }
        self.print_help(snps, "wipe", args=("disk_name",), params=params)
