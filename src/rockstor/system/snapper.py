"""
Snapper DBus helper methods
"""

from osi import run_command
from dbus import SystemBus, Interface, DBusException
from contextlib import contextmanager
from storageadmin.util import handle_exception
from rest_framework.exceptions import NotFound

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

    def get_config(self, name):
        """Apply some parsing to output of GetConfig, which returns a list of
        str, str, {} representing the name, subvolume and settings.
        """
        config = {}
        try:
            output = self.GetConfig(name)
        except:
            raise NotFound('Configuration \'%s\' not found.' % name)
        else:
            return self._parse_config(output)

    def _parse_config(self, raw):
        """Return the relevant options as a dictionary.
        """
        config = raw[2].copy()
        config['NAME'] = raw[0]
        config['SUBVOLUME'] = raw[1]
        return config
