"""
Views for all things related to snapper
"""

from rest_framework import views
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from system.snapper import Snapper

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


class SnapperConfigList(views.APIView):
    """List all snapper configurations or create a new one.
    """
    def get(self, request):
        return Response(snapper.config_list())

    def put(self, request, name):
        return


class SnapperConfigDetail(views.APIView):
    """Create/edit/delete a snapper configuration.
    """
    def get(self, request, name):
        try:
            config = snapper.get_config(name)
        except:
            raise NotFound('Configuration \'%s\' not found.' % name)
        else:
            return Response(config)

    def delete(self, request, name):
        return


class SnapperSnapshotList(views.APIView):
    def get(self, request, name):
        try:
            snapshot_list = snapper.list_snapshots(name)
        except:
            raise NotFound('Configuration \'%s\' not found.' % name)
        else:
            return Response(snapshot_list)
