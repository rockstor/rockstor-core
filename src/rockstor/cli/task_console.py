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
from rest_util import api_call
import time
import json


class TaskConsole(BaseConsole):

    def __init__(self, prompt):
        BaseConsole.__init__(self)
        self.greeting = 'Scheduler'
        self.pprompt = prompt
        self.prompt = ('%s %s>' % (self.pprompt, self.greeting))
        self.baseurl = BaseConsole.url + 'sm/tasks/'

    def do_list(self, args):
        print api_call(self.baseurl)

    def do_snap(self, args):
        """
        snap share_name name_prefix frequency
        """
        if (args is not None):
            fields = args.split()
            input_data = {'meta': {'share': fields[0],
                                   'prefix': fields[1],},
                          'name': 'snapshot',
                          'ts': time.time() + 120,
                          'frequency': fields[2],}
            print input_data
            headers = {'content-type': 'application/json'}
            snap_info = api_call(self.baseurl, data=json.dumps(input_data),
                                 calltype='post', headers=headers)
            print snap_info
        else:
            return self.do_help(args)

    def do_scrub(self, args):
        """
        scrub pool_name
        """
        if (args is None):
            return self.do_help(args)

        url = ('%sscrub' % self.baseurl)
        input_data = {'pool': args,}
        scrub_info = api_call(url, data=input_data, calltype='post')
        print scrub_info

    def do_delete(self, args):
        """
        delete event_id
        """
        if (args is None):
            return self.do_help(args)

        event_info = api_call(self.baseurl, data={'id': args,},
                              calltype='delete')
        print event_info

