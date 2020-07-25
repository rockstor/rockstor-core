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

import time
from base_console import BaseConsole
from rest_util import api_error, api_call


class BackupPluginConsole(BaseConsole):
    def __init__(self, prompt):
        BaseConsole.__init__(self)
        self.parent_prompt = prompt
        self.greeting = "%s BackupPlugin" % self.parent_prompt
        self.prompt = "%s>" % self.greeting
        self.url = "%splugin/backup" % BaseConsole.url

    @api_error
    def do_status(self, args):
        return self._plugin_command("status")

    @api_error
    def do_start(self, args):
        return self._plugin_command("start")

    @api_error
    def do_stop(self, args):
        return self._plugin_command("stop")

    def _plugin_command(self, command):
        """
        Current status of the plugin

        status
        """
        url = "%s/plugin/%s" % (self.url, command)
        print(api_call(url, calltype="post"))

    @api_error
    def do_add(self, args):
        """
        Add a new backup policy

        add name source_ip source_path dest_share email frequency num_retain
        """
        fields = args.split()
        input_data = {
            "name": fields[0],
            "source_ip": fields[1],
            "source_path": fields[2],
            "dest_share": fields[3],
            "notify_email": fields[4],
            "frequency": fields[5],
            "num_retain": fields[6],
            "ts": time.time() + 120,
        }
        headers = {"content-type": "application/json"}
        po = api_call(self.url, data=input_data, calltype="post", headers=headers)
        print(po)

    @api_error
    def do_list(self, args):
        """
        List all backup policies

        list
        """
        ro = api_call(self.url)
        print(ro)

    @api_error
    def do_delete(self, args):
        """
        Delete a backup policy

        delete policy_id
        """
        url = "%s/%s" % (self.url, args)
        po = api_call(url, calltype="delete")
        print(po)

    @api_error
    def do_toggle(self, args):
        """
        Enable or Disable a backup policy

        toggle policy_id <enable|disable>
        """
        fields = args.split()
        url = "%s/%s" % (self.url, fields[0])
        input_data = {
            "enabled": True,
        }
        if fields[1] == "disable":
            input_data["enabled"] = False
        headers = {"content-type": "application/json"}
        po = api_call(url, data=input_data, calltype="put", headers=headers)
        print(po)

    @api_error
    def do_trail(self, args):
        """
        Print the trail of a backup policy

        trail policy_id
        """
        url = "%s/trail/policy/%s" % (self.url, args)
        to = api_call(url)
        print(to)
