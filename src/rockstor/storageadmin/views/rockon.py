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

import requests
from rest_framework.response import Response
from django.db import transaction
from storageadmin.models import (RockOn, DImage, DContainer, DPort, DVolume,
                                 ContainerOption, DCustomConfig)
from storageadmin.serializers import RockOnSerializer
from storageadmin.util import handle_exception
import rest_framework_custom as rfc
from rockon_helpers import (docker_status, rockon_status)
import logging
logger = logging.getLogger(__name__)


class RockOnView(rfc.GenericView):
    serializer_class = RockOnSerializer

    def get_queryset(self, *args, **kwargs):
        for ro in RockOn.objects.all():
            if (ro.state == 'installed'):
                #update current running status of installed rockons.
                ro.status = rockon_status(ro.name)
                ro.save()
        return RockOn.objects.filter().order_by('-id')

    @transaction.atomic
    def put(self, request):
        with self._handle_exception(request):
            return Response()

    @transaction.atomic
    def post(self, request, command=None):
        with self._handle_exception(request):
            if (not docker_status()):
                e_msg = ('Rock-on service is not running. Start it and try '
                         'again')
                handle_exception(Exception(e_msg), request)

            if (command == 'update'):
                rockons = self._get_available(request)
                for r in rockons.keys():
                    name = r
                    ro = None
                    if (RockOn.objects.filter(name=name).exists()):
                        ro = RockOn.objects.get(name=name)
                        ro.description = rockons[r]['description']
                    else:
                        ro = RockOn(name=name,
                                    description=rockons[r]['description'],
                                    version='1.0', state='available',
                                    status='stopped')
                    ro.save()
                    containers = rockons[r]['containers']
                    for c in containers.keys():
                        io = None
                        iname = containers[c]['image']
                        if (DImage.objects.filter(name=iname).exists()):
                            io = DImage.objects.get(name=iname)
                        else:
                            io = DImage(name=iname, tag='latest', repo='foo')
                        io.save()

                        co = None
                        if (DContainer.objects.filter(name=c).exists()):
                            co = DContainer.objects.get(name=c)
                            co.dimage = io
                            co.rockon = ro
                        else:
                            co = DContainer(rockon=ro, dimage=io, name=c)
                        co.save()

                        if ('ports' in containers[c]):
                            ports = containers[c]['ports']
                            for p in ports.keys():
                                po = None
                                if (DPort.objects.filter(hostp=p).exists()):
                                    po = DPort.objects.get(hostp=p)
                                    po.container = co
                                else:
                                    po = DPort(hostp=p, containerp=p,
                                               container=co)
                                if (ports[p] == 'ui'):
                                    po.uiport = True
                                else:
                                    po.protocol = ports[p]
                                po.save()

                        if ('volumes' in containers[c]):
                            volumes = containers[c]['volumes']
                            for v in volumes:
                                if (not DVolume.objects.filter(
                                        dest_dir=v, container=co).exists()):
                                    vo = DVolume(container=co, dest_dir=v)
                                    vo.save()
                            for vo in DVolume.objects.filter(container=co):
                                if (vo.dest_dir not in volumes):
                                    vo.delete()

                        if ('opts' in containers[c]):
                            options = containers[c]['opts']
                            for o in options.keys():
                                if (not ContainerOption.objects.filter(
                                        container=co, name=options[o]).exists()):
                                    oo = ContainerOption(container=co, name=o,
                                                         val=options[o])
                                    oo.save()

                    if ('custom_config' in rockons[r]):
                        cc_d = rockons[r]['custom_config']
                        for k in cc_d:
                            cco, created = DCustomConfig.objects.get_or_create(
                                rockon=ro, key=k,
                                defaults={'description': cc_d[k]})
                            if (not created):
                                cco.description = cc_d[k]
                            if (not created and k == 'iprange' and ro.name == 'Plex'):
                                from storageadmin.models import NetworkInterface
                                try:
                                    ni = NetworkInterface.objects.filter(itype='management')[0]
                                    cco.val = ('%s/255.255.255.0' % ni.ipaddr)
                                except:
                                    pass
                            cco.save()
                    if ('app_link' in rockons[r]):
                        app_link = rockons[r]['app_link']
                        if (ro.state != 'installed'):
                            ro.link = app_link
                    if ('website' in rockons[r]):
                        ro.website = rockons[r]['website']
                    ro.save()
            return Response()

    def _get_available(self, request):
        msg = ('Network error while checking for updates. '
               'Please try again later.')
        with self._handle_exception(request, msg=msg):
            r = requests.get('http://rockstor.com/rockons.json')
            rockons = r.json()
            return rockons

    @transaction.atomic
    def delete(self, request, sname):
        with self._handle_exception(request):
            return Response()
