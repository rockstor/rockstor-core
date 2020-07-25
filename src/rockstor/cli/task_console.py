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
import time


class TaskConsole(BaseConsole):
    def __init__(self, prompt):
        BaseConsole.__init__(self)
        self.greeting = "Scheduler"
        self.pprompt = prompt
        self.prompt = "%s %s>" % (self.pprompt, self.greeting)
        self.baseurl = BaseConsole.url + "sm/tasks/"

    def do_types(self, args):
        """
        print all task types that can be scheduled
        """
        url = "%stypes" % self.baseurl
        print(api_call(url))

    def do_list(self, args):
        """
        print all scheduled tasks, or optionally for the given id.

        list <task_id>
        """
        url = self.baseurl
        if len(args) > 0:
            url = "%s%s" % (url, args)
        print(api_call(url))

    def do_log(self, args):
        """
        print all task logs, or optionally for the given task

        log <task_id>
        """
        url = "%slog" % self.baseurl
        if len(args) > 0:
            url = "%s/taskdef/%s" % (url, args)
        print(api_call(url))

    def do_snap(self, args):
        """
        snap share_name name_prefix frequency tag
        """
        if len(args) > 0:
            fields = args.split()
            input_data = {
                "meta": {"share": fields[0], "prefix": fields[1],},
                "task_type": "snapshot",
                "name": fields[3],
                "ts": time.time() + 120,
                "frequency": fields[2],
            }
            print(input_data)
            headers = {"content-type": "application/json"}
            snap_info = api_call(
                self.baseurl, data=input_data, calltype="post", headers=headers
            )
            print(snap_info)
        else:
            return self.do_help(args)

    def do_scrub(self, args):
        """
        scrub pool_name frequency tag
        """
        if len(args) == 0:
            return self.do_help(args)

        fields = args.split()
        input_data = {
            "meta": {"pool": fields[0]},
            "task_type": "scrub",
            "name": fields[2],
            "ts": time.time() + 120,
            "frequency": fields[1],
        }
        print(input_data)
        headers = {"content-type": "application/json"}
        scrub_info = api_call(
            self.baseurl, data=input_data, calltype="post", headers=headers
        )
        print(scrub_info)

    def _toggle_event(self, event_id, enabled=False):
        url = "%s/%s" % (self.baseurl, event_id)
        input_data = {
            "enabled": enabled,
        }
        print(api_call(url, data=input_data, calltype="put"))

    def do_disable(self, args):
        """
        disable an event.

        disable event_id
        """
        if len(args) == 0:
            return self.do_help(args)
        self._toggle_event(args)

    def do_enable(self, args):
        """
        enable an event

        eanble event_id
        """
        if len(args) == 0:
            return self.do_help(args)
        self._toggle_event(args, enabled=True)

    def do_delete(self, args):
        """
        delete event_id
        """
        if len(args) == 0:
            return self.do_help(args)
        url = "%s%s" % (self.baseurl, args)
        event_info = api_call(url, calltype="delete")
        print(event_info)
