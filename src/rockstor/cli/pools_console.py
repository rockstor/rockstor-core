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
from rest_util import (api_error, api_call, print_pools_info, print_pool_info)


class PoolsConsole(BaseConsole):

    def __init__(self, prompt):
        BaseConsole.__init__(self)
        self.pprompt = prompt
        self.prompt = prompt + ' Pools> '
        self.url = ('%spools' % BaseConsole.url)

    @api_error
    def do_list(self, args):
        url = self.url+'?format=json'
        if (args):
            # print info for a single pool
            url = ('%s/%s' % (self.url, args))
            pool_info = api_call(url)
            print_pool_info(pool_info, True)
        else:
            pools_info = api_call(url)
            print_pools_info(pools_info)

    def help_list(self):
        print """
        %(c)sDisplay information about pools on the appliance.%(e)s

        Details of all pools:     %(c)slist%(e)s
        Details of a single pool: %(c)slist%(e)s %(u)spool_name%(e)s
        
        %(c)sParameters%(e)s
        %(u)spool_name%(e)s    If this optional parameter is given, 
                     details are printed for the given pool only.
        """ % BaseConsole.c_params

    @api_error
    def do_add(self, args):
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

    def help_add(self):
        print """
        %(c)sCreate a new pool.%(e)s

        Create a new pool: %(c)sadd%(e)s %(u)spool_name%(e)s %(u)sdisk_list%(e)s %(u)raid_type%(e)s

        %(c)sParameters%(e)s
        %(u)spool_name%(e)s    Intended name of the pool.
        %(u)sdisk_list%(e)s    A list of comma-separated(no whitespace) disks. For
                    example: sdb,sdc.
        %(u)sraid_type%(e)s    One of the following: single, raid0, raid1 and raid10

        %(c)sExamples%(e)s
        To create a raid0 pool with two disks(sdb and sdc) called pool0
        %(c)sadd%(e)s pool0 sdb,sdc raid0
        """ % BaseConsole.c_params

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
        print "Deleting pool %s" % args[0]
        pool_info = api_call(url, calltype='delete')
        print "Pool %s deleted" % args[0]

    def help_delete(self):
        print """
        %(c)sDelete a pool.%(e)s

        Delete a pool: %(c)sdelete%(e)s %(u)spool_name%(e)s

        %(c)sParameters%(e)s
        %(u)spool_name%(e)s    Name of a valid pool to delete.

        %(c)sExample%(e)s
        To delete a pool named pool0
        %(c)sdelete%(e)s pool0
        """ % BaseConsole.c_params


    @api_error
    def do_console(self, args):
        pd_console = PoolDetailConsole('foo')
        input_pool = args.split()
        if (len(input_pool) > 0):
            pd_console.set_prompt(input_pool[0])
            pd_console.cmdloop()
        else:
            pd_console.onecmd(args)

    def help_console(self):
        print """
        %(c)sSubconsole for a single pool%(e)s

        To go to a particular pool's exclusive subconsole: %(c)sconsole%(e)s %(u)spool_name%(e)s

        %(c)sParameters%(e)s
        %(u)spool_name%(e)s    Name of a valid pool.

        %(c)sExample%(e)s
        To perform operations on a pool called mypool inside it's exclusive
        subconsole
        %(c)sconsole%(e)s mypool
        """

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
