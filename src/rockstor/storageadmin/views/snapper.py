"""
Views for all things related to snapper
"""

from dbus import DBusException
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework import status
from system.snapper import Snapper
import rest_framework_custom as rfc

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

# Obtain snapper interface
snapper = Snapper()


class SnapperConfigList(rfc.GenericAPIView):
    """List all snapper configurations or create a new one.
    """
    def get(self, request):
        return Response(snapper.config_list())

    def post(self, request):
        with self._handle_exception('Failed to create configuration'):
            name = request.data.get('NAME')
            subvolume = request.data.get('SUBVOLUME')
            snapper.CreateConfig(name, subvolume, 'btrfs', 'default')
        return Response(request.data, status=status.HTTP_201_CREATED)


class SnapperConfigDetail(rfc.GenericAPIView):
    """Create/edit/delete a snapper configuration.
    """
    def get(self, request, name):
        try:
            config = snapper.get_config(name)
        except DBusException:
            raise NotFound('Configuration \'%s\' not found.' % name)
        else:
            return Response(config)

    def delete(self, request, name):
        with self._handle_exception('Failed to delete configuration'):
            snapper.DeleteConfig(name)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SnapperSnapshotList(rfc.GenericAPIView):
    """Return the list of snapshots for the given snapper configuration.
    """
    def get(self, request, name):
        try:
            snapshot_list = snapper.list_snapshots(name)
        except DBusException:
            raise NotFound('Configuration \'%s\' not found.' % name)
        else:
            return Response(snapshot_list)


class SnapperSnapshotDetail(rfc.GenericAPIView):
    """Return information about a specific snapshot.
    """
    def get(self, request, name, number):
        try:
            snapshot = snapper.get_snapshot(name, number)
        except DBusException as e:
            raise NotFound(e)
        else:
            return Response(snapshot)
