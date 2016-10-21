"""
Snapper DBus helper methods
"""

from osi import run_command
from dbus import SystemBus, Interface, DBusException
from time import gmtime, asctime
from pwd import getpwuid
from storageadmin.util import handle_exception

"""
Copyright (c) 2016 RockStor, Inc. <http://rockstor.com>
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


class Snapper(Interface):
    """Extend the default snapper DBus interface with some output conversion
    methods.
    """
    def __init__(self):
        try:
            bus = SystemBus()
            super(Snapper, self).__init__(
                bus.get_object('org.opensuse.Snapper',
                               '/org/opensuse/Snapper'),
                dbus_interface='org.opensuse.Snapper')
        except DBusException as e:
            handle_exception(e, None, 'Could not connect to snapperd')

    def config_list(self):
        return [self._parse_config(config) for config in self.ListConfigs()]

    def get_config(self, config):
        """Apply some parsing to output of GetConfig, which returns a list of
        str, str, {} representing the name, subvolume and settings.
        """
        output = self.GetConfig(config)
        return self._parse_config(output)

    def list_snapshots(self, config):
        """Return snapshot information as a list of dictionaries.
        """
        snapshots = self.ListSnapshots(config)
        snapshot_list = []

        for snapshot in snapshots:
            # If this snapshot has a pre-number, combine its data with the
            # previous snapshot and don't make a new entry.
            if snapshot[2]:
                data = snapshot_list[-1]
                data['number'] += ', %s' % snapshot[0]
                data['end_time'] = self._parse_timestamp(snapshot[3])
                data['type'] += ', post'
                continue

            snapshot_list.append(self._parse_snapshot(config, snapshot))

        return snapshot_list

    def get_snapshot(self, config, number):
        """Return single snapshot information.
        """
        snapshot = self.GetSnapshot(config, number)
        return self._parse_snapshot(config, snapshot)

    def _parse_config(self, raw):
        """Return the relevant options as a dictionary.
        """
        config = raw[2].copy()
        config['NAME'] = raw[0]
        return config

    def _parse_snapshot(self, config, snapshot):
        """Parse raw snapshot data.

        The output produced by snapper is a list with the following elements:
            int: snapshot number
            int: snapshot type (0 = single, 1 = pre, 2 = post)
            int: pre-number if a post snapshot, else 0
            int: -1 or timestamp in seconds since Unix epoch
            int: uid
            str: description
            str: cleanup algorithm
            dict: userdata
        Also append the config name to make it function as a nested resource.
        """
        return {
            'number': str(snapshot[0]),
            'type': ['single', 'pre', 'post'][snapshot[1]],
            'start_time': self._parse_timestamp(snapshot[3]),
            'end_time': '',
            'user': getpwuid(snapshot[4])[0],
            'description': snapshot[5],
            'cleanup': snapshot[6],
            'userdata': snapshot[7].copy(),
            'config': config
        }

    def _parse_timestamp(self, t):
        """Convert a snapshot timestamp to human-readable format.

        Snapper reports either an integer representing seconds since UNIX
        epoch, or -1 for the "current" snapshot.
        """
        return asctime(gmtime(t)) if t != -1 else ''
