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
                                 ContainerOption)
from storageadmin.serializers import RockOnSerializer
from storageadmin.util import handle_exception
import rest_framework_custom as rfc
from rockon_helpers import docker_status
import logging
logger = logging.getLogger(__name__)


class RockOnView(rfc.GenericView):
    serializer_class = RockOnSerializer

    def get_queryset(self, *args, **kwargs):
        return RockOn.objects.all()

    @transaction.commit_on_success
    def put(self, request):
        with self._handle_exception(request):
            return Response()

    @transaction.commit_on_success
    def post(self, request, command=None):
        with self._handle_exception(request):
            if (not docker_status()):
                e_msg = ('Rock-on service is not running. Start it and try '
                         'again')
                handle_exception(Exception(e_msg), request)

            if (command == 'update'):
                rockons = self._get_available()
                for r in rockons.keys():
                    name = r
                    ro = None
                    if (RockOn.objects.filter(name=name).exists()):
                        ro = RockOn.objects.get(name=name)
                    else:
                        ro = RockOn(name=name, version='1.0',
                                    state='available', status='stopped')
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

                        ports = containers[c]['ports']
                        for p in ports.keys():
                            po = None
                            if (Port.objects.filter(hostp=p).exists()):
                                po = Port.objects.get(hostp=p)
                                po.container = co
                                po.protocol = ports[p]
                            else:
                                po = Port(hostp=p, containerp=p,
                                          container=co, protocol=ports[p])
                            po.save()
                        volumes = containers[c]['volumes']
                        for v in volumes:
                            if (not Volume.objects.filter(
                                    dest_dir=v, container=co).exists()):
                                vo = Volume(container=co, dest_dir=v)
                                vo.save()
                        options = containers[c]['opts']
                        for o in options.keys():
                            if (not ContainerOption.objects.filter(
                                    container=co, name=options[o]).exists()):
                                oo = ContainerOption(container=co, name=o,
                                                     val=options[o])
                                oo.save()
            return Response()

    def _get_available(self):
        import requests
        r = requests.get('http://rockstor.com/rockons.json')
        rockons = r.json()
        return rockons

    @transaction.commit_on_success
    def delete(self, request, sname):
        with self._handle_exception(request):
            return Response()
