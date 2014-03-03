"""
Copyright (c) 2012-2014 RockStor, Inc. <http://rockstor.com>
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

from rest_framework.response import Response
from system.services import superctl
from generic_view import GenericView


class PluginView(GenericView):

    def post(self, request, command):
        """
        valid commands are status, off and on.
        """
        try:
            out, err, rc = superctl('backup-plugin', command)
            return Response({'status': out[0].split()[1],})
        except:
            return Response({'error': err,})


