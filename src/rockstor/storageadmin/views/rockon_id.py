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

import time
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q
from storageadmin.models import (RockOn, DContainer, DVolume, Share, DPort,
                                 DCustomConfig)
from storageadmin.serializers import RockOnSerializer
import rest_framework_custom as rfc
from storageadmin.util import handle_exception
from rockon_helpers import (docker_status, start, stop, install, uninstall, update)
from system.services import superctl

import logging
logger = logging.getLogger(__name__)


class RockOnIdView(rfc.GenericView):
    serializer_class = RockOnSerializer

    def get_queryset(self, *args, **kwargs):
        return RockOn.objects.all()

    @staticmethod
    def _pending_check(request):
        if (RockOn.objects.filter(state__contains='pending').exists()):
            e_msg = ('Another Rockon is in state transition. Multiple '
                     'simultaneous Rockon transitions are not '
                     'supported. Please try again later.')
            handle_exception(Exception(e_msg), request)

    @transaction.atomic
    def post(self, request, rid, command):
        with self._handle_exception(request):

            if (not docker_status()):
                e_msg = ('Docker service is not running. Start it and try '
                         'again.')
                handle_exception(Exception(e_msg), request)

            try:
                rockon = RockOn.objects.get(id=rid)
            except:
                e_msg = ('Rock-on(%d) does not exist' % rid)
                handle_exception(Exception(e_msg), request)

            try:
                dname = 'ztask-daemon'
                e_msg = ('ztask daemon is not running and could not be started')
                o, e, rc = superctl(dname, 'status')
                if (rc == 1):
                    superctl(dname, 'restart')
                    time.sleep(5)
            except Exception, e:
                logger.exception(e)
                handle_exception(Exception(e_msg), request)
            finally:
                if (rc == 1):
                    o, e, rc = superctl(dname, 'status')
                    if (rc == 1):
                        handle_exception(Exception(e_msg), request)

            if (command == 'install'):
                self._pending_check(request)
                share_map = request.data.get('shares', {})
                port_map = request.data.get('ports', {})
                cc_map = request.data.get('cc', {})
                containers = DContainer.objects.filter(rockon=rockon)
                for co in containers:
                    for s in share_map.keys():
                        sname = share_map[s]
                        if (not Share.objects.filter(name=sname).exists()):
                            e_msg = ('Invalid Share(%s).' % sname)
                            handle_exception(Exception(e_msg), request)
                        if (DVolume.objects.filter(container=co, dest_dir=s).exists()):
                            so = Share.objects.get(name=sname)
                            vo = DVolume.objects.get(container=co,
                                                     dest_dir=s)
                            vo.share = so
                            vo.save()
                    # {'host_port' : 'container_port', ... }
                    for p in port_map.keys():
                        if (DPort.objects.filter(hostp=p).exists()):
                            po = DPort.objects.get(hostp=p)
                            if (po.container.rockon.id != rockon.id):
                                e_msg = ('Rockon port(%s) is dedicated to '
                                         'another Rock-On(%s) and cannot '
                                         'be changed. Choose a different name'
                                         % (p, po.container.rockon.name))
                                handle_exception(Exception(e_msg), request)
                        else:
                            for co2 in DContainer.objects.filter(rockon=rockon):
                                if (DPort.objects.filter(container=co2, containerp=port_map[p]).exists()):
                                    po = DPort.objects.get(container=co2, containerp=port_map[p])
                                    po.hostp = p
                                    po.save()
                    for c in cc_map.keys():
                        if (not DCustomConfig.objects.filter(rockon=rockon, key=c).exists()):
                            e_msg = ('Invalid custom config key(%s)' % c)
                            handle_exception(Exception(e_msg), request)
                        cco = DCustomConfig.objects.get(rockon=rockon, key=c)
                        cco.val = cc_map[c]
                        cco.save()
                install.async(rockon.id)
                rockon.state = 'pending_install'
                rockon.save()
            elif (command == 'uninstall'):
                self._pending_check(request)
                if (rockon.state != 'installed'):
                    e_msg = ('Rock-on(%s) is not currently installed. Cannot '
                             'uninstall it' % rid)
                    handle_exception(Exception(e_msg), request)
                if (rockon.status == 'started' or rockon.status == 'pending_start'):
                    e_msg = ('Rock-on(%s) must be stopped before it can '
                             'be uninstalled. Stop it and try again' %
                             rid)
                    handle_exception(Exception(e_msg), request)
                uninstall.async(rockon.id)
                rockon.state = 'pending_uninstall'
                rockon.save()
                for co in DContainer.objects.filter(rockon=rockon):
                    DVolume.objects.filter(container=co, uservol=True).delete()
            elif (command == 'update'):
                self._pending_check(request)
                if (rockon.state != 'installed'):
                    e_msg = ('Rock-on(%s) is not currently installed. Cannot '
                             'update it' % rid)
                    handle_exception(Exception(e_msg), request)
                if (rockon.status == 'started' or rockon.status == 'pending_start'):
                    e_msg = ('Rock-on(%s) must be stopped before it can '
                             'be updated. Stop it and try again' %
                             rid)
                    handle_exception(Exception(e_msg), request)
                share_map = request.data.get('shares')
                for co in DContainer.objects.filter(rockon=rockon):
                    for s in share_map.keys():
                        sname = share_map[s]
                        if (not Share.objects.filter(name=sname).exists()):
                            e_msg = ('Invalid Share(%s).' % sname)
                            handle_exception(Exception(e_msg), request)
                        so = Share.objects.get(name=sname)
                        if (DVolume.objects.filter(container=co, share=so).exists()):
                            e_msg = ('Share(%s) is already assigned to this Rock-on' % sname)
                            handle_exception(Exception(e_msg), request)
                        if (DVolume.objects.filter(container=co, dest_dir=s).exists()):
                            e_msg = ('Directory(%s) is already mapped for this Rock-on' % s)
                            handle_exception(Exception(e_msg), request)
                        do = DVolume(container=co, share=so, uservol=True, dest_dir=s)
                        do.save()
                rockon.state = 'pending_update'
                rockon.save()
                update.async(rockon.id)
            elif (command == 'stop'):
                stop.async(rockon.id)
                rockon.status = 'pending_stop'
                rockon.save()
            elif (command == 'start'):
                start.async(rockon.id)
                rockon.status = 'pending_start'
                rockon.save()
            elif (command == 'state_update'):
                state = request.data.get('new_state')
                rockon.state = state
                rockon.save()
            elif (command == 'status_update'):
                status = request.data.get('new_status')
                rockon.status = status
                rockon.save()
            return Response(RockOnSerializer(rockon).data)
