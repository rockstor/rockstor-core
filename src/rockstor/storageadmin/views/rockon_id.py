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

from rest_framework.response import Response
from django.db import transaction
from storageadmin.models import (RockOn, DImage, DContainer, Port, Volume,
                                 ContainerOption, Share)
from storageadmin.serializers import RockOnSerializer
import rest_framework_custom as rfc
from storageadmin.util import handle_exception
from rockon_helpers import (docker_status, start, stop, install, uninstall)

import logging
logger = logging.getLogger(__name__)


class RockOnIdView(rfc.GenericView):
    serializer_class = RockOnSerializer

    def get_queryset(self, *args, **kwargs):
        return RockOn.objects.all()

    @transaction.commit_on_success
    def post(self, request, rid, command):
        with self._handle_exception(request):

            if (not docker_status()):
                e_msg = ('Rock-on service is not running. Start it and try '
                         'again')
                handle_exception(Exception(e_msg))

            try:
                rockon = RockOn.objects.get(id=rid)
            except:
                e_msg = ('Rock-on(%d) does not exist' % rid)
                handle_exception(Exception(e_msg), request)

            if (command == 'install'):
                containers = DContainer.objects.filter(rockon=rockon)
                for co in containers:
                    share_map = request.DATA.get('shares')
                    share_map = {'ovconfig': '/etc/openvpn', }
                    logger.debug('share map = %s' % share_map)
                    for s in share_map.keys():
                        if (not Share.objects.filter(name=s).exists()):
                            e_msg = ('Invalid Share(%s).' % s)
                            handle_exception(Exception(e_msg), request)
                        so = Share.objects.get(name=s)
                        vo = Volume.objects.get(container=co,
                                                dest_dir=share_map[s])
                        vo.share = so
                        vo.save()
                install.async(rockon.id)
                rockon.state = 'pending_install'
                rockon.save()
            elif (command == 'uninstall'):
                if (rockon.state != 'installed'):
                    e_msg = ('Rock-on(%s) is not currently installed. Cannot '
                             'uninstall it' % rid)
                    handle_exception(Exception(e_msg), request)
                if (rockon.status != 'stopped'):
                    e_msg = ('Rock-on(%s) must be stopped before it can '
                             'be uninstalled. Stop it and try again' %
                             rid)
                    handle_exception(Exception(e_msg), request)
                uninstall.async(rockon.id)
                rockon.state = 'uninstall_pending'
                rockon.save()
            elif (command == 'stop'):
                stop.async(rockon.id)
                rockon.status = 'stop_pending'
                rockon.save()
            elif (command == 'start'):
                start.async(rockon.id)
                rockon.status = 'start_pending'
                rockon.save()
            elif (command == 'state_update'):
                state = request.DATA.get('new_state')
                rockon.state = state
                rockon.save()
            elif (command == 'status_update'):
                status = request.DATA.get('new_status')
                rockon.status = status
                rockon.save()
            return Response(RockOnSerializer(rockon).data)
