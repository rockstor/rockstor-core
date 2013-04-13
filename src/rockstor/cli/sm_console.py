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

class SMConsole(BaseConsole):

    def __init__(self, prompt):
        BaseConsole.__init__(self)
        self.greeting = 'Smart Manager'
        self.pprompt = prompt
        self.prompt = ('%s %s>' % (self.pprompt, self.greeting))
        self.baseurl = BaseConsole.url + 'sm/stap/'

    def do_list(self, args):
        url = self.baseurl
        if (args is not None):
            tap_fields = args.split()
            if (len(tap_fields) > 0):
                url = url + tap_fields[0] + '/'
        stap_info = api_call(url)
        print stap_info

    def do_run(self, args):
        tap_fields = args.split()
        if (len(tap_fields) > 0):
            tname = tap_fields[0]
            url = ('%ssm/stap/%s/' % (BaseConsole.url, tname))
            stap_info = api_call(url, data=None, calltype='post')
            print stap_info
        else:
            return self.do_help(args)
