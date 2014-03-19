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

from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
import rest_framework_custom as rfc
from storageadmin.util import handle_exception
from storageadmin.models import (Plugin, InstalledPlugin)
from storageadmin.serializers import PluginSerializer
import time

import logging
logger = logging.getLogger(__name__)

class PluginView(rfc.GenericView):
    serializer_class = PluginSerializer

    def get_queryset(self, *args, **kwargs):
        return  Plugin.objects.all()

        #if 'available_plugins' in request.session:
        #    if request.session['available_plugins'] == None:
        #        request.session['available_plugins'] = ['backup']
        #else:
        #    request.session['available_plugins'] = ['backup']

        #if 'installed_plugins' in request.session:
        #    if request.session['installed_plugins'] == None:
        #        request.session['installed_plugins'] = []
        #else:
        #    request.session['installed_plugins'] = []

        #data = {
        #        'installed': request.session['installed_plugins'],
        #        'available': request.session['available_plugins']
        #        }
        #return Response(data)

