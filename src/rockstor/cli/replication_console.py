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
from rest_util import api_call


class ReplicationConsole(BaseConsole):
    def __init__(self, prompt):
        BaseConsole.__init__(self)
        self.parent_prompt = prompt
        self.greeting = "%s Replication" % self.parent_prompt
        self.prompt = "%s>" % self.greeting
        self.url = "%ssm/replicas/" % BaseConsole.url

    def do_add(self, args):
        """
        Add a new replication job for a share

        add share_name target_appliance_ip target_pool frequency
        """
        fields = args.split()
        input_data = {
            "share": fields[0],
            "appliance": fields[1],
            "pool": fields[2],
            "frequency": fields[3],
        }
        ro = api_call(self.url, data=input_data, calltype="post")
        print(ro)

    def do_list(self, args):
        """
        List all replication jobs, or optionally for a share

        list <share_name>
        """
        ro = api_call(self.url)
        print(ro)

    def do_enable(self, args):
        """
        Enable replication (idempotent if already enabled)

        enable replica_id
        """
        input_data = {
            "enabled": True,
        }
        url = "%s%s" % (self.url, args)
        ro = api_call(url, data=input_data, calltype="put")
        print(ro)

    def do_disable(self, args):
        """
        Disable replication (idempotent if already disabled)

        disable replica_id
        """
        input_data = {
            "enabled": False,
        }
        url = "%s%s" % (self.url, args)
        ro = api_call(url, data=input_data, calltype="put")
        print(ro)
