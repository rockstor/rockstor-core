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
from rest_util import (api_call, print_pool_info)


class PoolsConsole(BaseConsole):

    def __init__(self, prompt):
        BaseConsole.__init__(self)
        self.parent_prompt = prompt
        self.greeting = ('%s Pools' % self.parent_prompt)
        self.prompt = ('%s>' % self.greeting)
        self.url = ('%spools/' % BaseConsole.url)

    def do_list(self, args):
        """
        List brief information about all pools

        """
        pool_info = api_call(self.url)
        print_pool_info(pool_info)

    def do_add(self, args):
        """
        To add a pool:

        add -dsdb,sdc -rraid0 -npool0
        """
        arg_fields = args.split()
        input_data = {}
        for f in arg_fields:
            if(f[0:2] == '-d'):
                input_data['disks'] = f[2:]
            elif(f[0:2] == '-r'):
                input_data['raid_level'] = f[2:]
            elif(f[0:2] == '-n'):
                input_data['name'] = f[2:]
            else:
                return self.do_help(args)
        if(len(input_data) != 3):
            return self.do_help(args)
        url = ('%s%s/' % (self.url, input_data['name']))
        pool_info = api_call(url, data=input_data, calltype='post')
        print_pool_info(pool_info)

    def do_delete(self, args):
        """
        To delete a pool:

        delete pool0
        """
        input_pool_list = args.split()
        if (len(input_pool_list) > 0):
            url = ('%s%s/' % (self.url, input_pool_list[0]))
            pool_info = api_call(url, calltype='delete')
            print pool_info

    def do_pool(self, args):
        """
        To go to a pool console: pool pool_name
        """
        pd_console = PoolDetailConsole('foo')
        input_pool = args.split()
        if (len(input_pool) > 0):
            pd_console.set_prompt(input_pool[0])
            pd_console.cmdloop()
        else:
            pd_console.onecmd(args)

