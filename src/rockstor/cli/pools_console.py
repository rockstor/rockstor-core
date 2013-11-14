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


import json

from base_console import BaseConsole
from pool_detail_console import PoolDetailConsole
from rest_util import (api_error, api_call, print_pool_info)


class PoolsConsole(BaseConsole):

    def __init__(self, prompt):
        BaseConsole.__init__(self)
        self.pprompt = prompt
        self.prompt = ('%s Pools>' % self.pprompt)
        self.url = ('%spools' % BaseConsole.url)

    @api_error
    def do_list(self, args):
        """
        List brief information about pools

        Details of all pools:     list
        Details of a single pool: list <pool_name>
        """
        url = self.url+'?format=json'
        if (args is not None):
            url = ('%s%s' % (self.url, args))
        pool_info = api_call(url)
        print_pool_info(pool_info)

    @api_error
    def do_add(self, args):
        """
        Create a new pool.

        Create a new pool: add pool_name disk_list raid_type

        Parameters:
        pool_name:    Intended name of the pool.
        disk_list:    A list of comma-separated(no whitespace) disks. For
                      example: sdb,sdc.
        raid_type:    One of the following: single, raid0, raid1 and raid10

        Examples:
        To create a raid0 pool with two disks(sdb and sdc) called pool0
            add pool0 sdb,sdc raid0
        """
        arg_fields = args.split()
        if (len(arg_fields) < 3):
            error = '3 arguments expected. %d given' % len(arg_fields)
            return self.help_wrapper(error, 'add')

        input_data = {'pname': arg_fields[0],
                      'disks': arg_fields[1],
                      'raid_level': arg_fields[2]}
        url = (self.url)
        pool_info = api_call(url, data=input_data, calltype='post')
        print_pool_info(pool_info)

    @api_error
    def do_delete(self, args):
        """
        Delete a pool.

        Delete a pool: delete pool_name

        Parameters:
        pool_name:    Name of a valid pool to delete.

        Example:
        To delete a pool named pool0
            delete pool0
        """
        if (len(args) == 0):
            return self.help_wrapper('missing pool_name', 'delete')
        url = ('%s/%s' % (self.url, args))
        pool_info = api_call(url, calltype='delete')
        print pool_info

    @api_error
    def do_console(self, args):
        """
        Subconsole for a single pool.

        To go to a particular
        pool's exclusive subconsole: console pool_name

        Parameters:
        pool_name:    Name of a valid pool.

        Example:
        To perform operations on a pool called mypool inside it's exclusive
        subconsole
            console mypool
        """
        pd_console = PoolDetailConsole('foo')
        input_pool = args.split()
        if (len(input_pool) > 0):
            pd_console.set_prompt(input_pool[0])
            pd_console.cmdloop()
        else:
            pd_console.onecmd(args)

    @api_error
    def do_scrub(self, args):
        """
        To scrub a pool:

        scrub pool0
        """
        if (len(args) == 0):
            return self.help_wrapper('missing pool_name', 'scrub')
        url = ('%s/%s/scrub' % (self.url, args))
        scrub_info = api_call(url, calltype='post')
        print scrub_info

    @api_error
    def do_scrub_status(self, args):
        """
        get scrub status for a pool

        scrub_status pool0
        """
        if (len(args) == 0):
            return self.help_wrapper('missing pool_name', 'scrub_status')
        url = ('%s/%s/scrub/status' % (self.url, args))
        scrub_info = api_call(url, calltype='post')
        print scrub_info
