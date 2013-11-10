"""
Copyright (c) 2012-2013 RockStor, Inc. <http://rockstor.com>
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
from rest_util import (api_error, api_call, print_disk_info)
from storageadmin.exceptions import RockStorAPIException


class DisksConsole(BaseConsole):

    def __init__(self, prompt):
        BaseConsole.__init__(self)
        self.prompt = prompt + ' Disks>'
        self.baseurl = ('%sdisks' % BaseConsole.url)

    @api_error
    def do_list(self, args):
        """
        List brief information about disks in the system.

        Details of all disks:     list
        Details of a single disk: list <disk_name>

        Parameters:
        disk_name: If this optional parameter is given, details are printed
                   for the given disk only.

        Examples:
        Print information of all disks in the system
            list

        Print information for the disk sdd
            list sdd
        """
        url = self.baseurl
        if (args is not None):
            url = ('%s%s' % (url, args))
        disk_info = api_call(url)
        print_disk_info(disk_info)

    @api_error
    def do_scan(self, args):
        """
        Scan the system for any new disks since the last scan.

        Example:
        Scan the system for any new disks:
            scan
        """
        url = ('%s/scan' % self.baseurl)
        disk_info = api_call(url, data=None, calltype='post')
        print_disk_info(disk_info)

    @api_error
    def do_delete(self, args):
        """
        Delete a offlined disk

        delete disk_name
        """
        url = ('%s/%s' % (self.baseurl, args))
        api_call(url, calltype='delete')
        print_disk_info(api_call(self.baseurl))

    @api_error
    def do_wipe(self, args):
        """
        Wipe the partition table of a disk. This is required for
        used/partitioned disks to be usable by rockstor.

        wipe disk_name
        """
        url = ('%s/%s/wipe' % (self.baseurl, args))
        api_call(url, calltype='post')
        print_disk_info(api_call(self.baseurl))

