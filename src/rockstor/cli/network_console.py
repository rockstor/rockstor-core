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

class NetworkConsole(BaseConsole):

    def __init__(self, prompt):
        BaseConsole.__init__(self)
        self.prompt = prompt + ' Network>'

    def do_list(self, args):
        pass

    def do_scan(self, args):
        url = ('%s/network/' % BaseConsole.url)
        network_info = api_call(url, calltype='post')
        print network_info

    def do_config(self, args):
        pass

