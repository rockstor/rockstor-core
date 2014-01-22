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
from generic_view import GenericView
from storageadmin.util import handle_exception
import time

import logging
logger = logging.getLogger(__name__)

class PluginView(GenericView):

    def get(self, request):
        if 'available_plugins' in request.session:
            if request.session['available_plugins'] == None:
                request.session['available_plugins'] = ['backup']
        else:
            request.session['available_plugins'] = ['backup']

        if 'installed_plugins' in request.session:
            if request.session['installed_plugins'] == None:
                request.session['installed_plugins'] = []
        else:
            request.session['installed_plugins'] = []

        data = {
                'installed': request.session['installed_plugins'], 
                'available': request.session['available_plugins']
                }
        return Response(data)

    def post(self, request):
        try:
            plugin_name = request.DATA['plugin_name']
            logger.debug('plugin_name is %s' % plugin_name)
            installed_plugins = request.session['installed_plugins']
            installed_plugins.append(plugin_name)
            request.session['installed_plugins'] = installed_plugins
            logger.debug('installed_plugins in plugin.py is %s' % request.session['installed_plugins'])
            time.sleep(10)
            return Response()
        except Exception, e:
            handle_exception(e, request)
            

