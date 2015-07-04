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
                                 ContainerOption, DCustomConfig, DContainerLink)
from storageadmin.serializers import RockOnSerializer
from storageadmin.util import handle_exception
import rest_framework_custom as rfc
from rockon_helpers import (docker_status, rockon_status)
from django_ztask.models import Task
import pickle
import re
import logging
logger = logging.getLogger(__name__)


class RockOnView(rfc.GenericView):
    serializer_class = RockOnSerializer

    def get_queryset(self, *args, **kwargs):
        if (docker_status()):
            pending_rids = []
            for t in Task.objects.all():
                pending_rids.append(pickle.loads(t.args)[0])
            for ro in RockOn.objects.all():
                if (ro.state == 'installed'):
                    # update current running status of installed rockons.
                    if (ro.id not in pending_rids):
                        ro.status = rockon_status(ro.name)
                elif (re.search('pending', ro.state) is not None and
                      ro.id not in pending_rids):
                    # reset rockons to their previous state if they are stuck
                    # in a pending transition.
                    if (re.search('uninstall', ro.state) is not None):
                        ro.state = 'installed'
                    else:
                        ro.state = 'available'
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
                    if (r != 'OwnCloud'):
                        continue
                    name = r
                    r_d = rockons[r]
                    ui_d = r_d['ui']
                    ro = None
                    if (RockOn.objects.filter(name=name).exists()):
                        ro = RockOn.objects.get(name=name)
                        logger.debug('ro state = %s' % ro.state)
                        if (ro.state == 'installed' or (re.match('pending', ro.state) is not None)):
                            #don't update metadata if it's installed or in some pending state.
                            logger.debug('Rock-On(%s) is either installed or '
                                         'in pending state. Skipping update.' %
                                         name)
                            continue
                        ro.description = r_d['description']
                        ro.website = r_d['website']
                        ro.icon = r_d['icon']
                        ro.volume_add_support = r_d['volume_add_support']
                        ro.more_info = r_d['more_info']
                    else:
                        ro = RockOn(name=name,
                                    description=r_d['description'],
                                    version='1.0', state='available',
                                    status='stopped', website=r_d['website'],
                                    icon=r_d['icon'], volume_add_support=r_d['volume_add_support'],
                                    more_info=r_d['more_info'])
                    if ('ui' in r_d):
                        ui_d = r_d['ui']
                        ro.link = ui_d['slug']
                        ro.https = ui_d['https']
                    ro.save()
                    containers = r_d['containers']
                    for c in containers.keys():
                        io = None
                        c_d = containers[c]
                        iname = c_d['image']
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
                            co.launch_order = c_d['launch_order']
                        else:
                            co = DContainer(rockon=ro, dimage=io, name=c,
                                            launch_order=c_d['launch_order'])
                        co.save()


                        if ('ports' in containers[c]):
                            ports = containers[c]['ports']
                            for p in ports.keys():
                                p_d = ports[p]
                                p = int(p)
                                po = None
                                if (DPort.objects.filter(containerp=p, container=co).exists()):
                                    po = DPort.objects.get(containerp=p, container=co)
                                    po.hostp_default = p_d['host_default']
                                    po.description = p_d['description']
                                    po.protocol = p_d['protocol']
                                    po.label = p_d['label']
                                else:
                                    #let's find next available default if default is already taken
                                    def_hostp = p_d['host_default']
                                    while (True):
                                        if (DPort.objects.filter(hostp=def_hostp).exists()):
                                            def_hostp += 1
                                        else:
                                            break
                                    po = DPort(description=p_d['description'],
                                               hostp=def_hostp, containerp=p,
                                               hostp_default=def_hostp,
                                               container=co,
                                               protocol=p_d['protocol'],
                                               label=p_d['label'])
                                if ('ui' in p_d):
                                    po.uiport = p_d['ui']
                                if (po.uiport):
                                    ro.ui = True
                                    ro.save()
                                po.save()
                        else:
                            ports = {}
                        ports = [int(p) for p in ports]
                        for po in DPort.objects.filter(container=co):
                            if (po.containerp not in ports):
                                po.delete()

                        v_d = {}
                        if ('volumes' in c_d):
                            v_d = c_d['volumes']
                            for v in v_d.keys():
                                cv_d = v_d[v]
                                if (DVolume.objects.filter(dest_dir=v, container=co).exists()):
                                    vo = DVolume.objects.get(dest_dir=v, container=co)
                                    vo.description = cv_d['description']
                                    vo.label = cv_d['label']
                                    vo.min_size = cv_d['min_size']
                                    vo.save()
                                else:
                                    vo = DVolume(container=co, dest_dir=v, description=cv_d['description'],
                                                 min_size=cv_d['min_size'], label=cv_d['label'])
                                    vo.save()

                        logger.debug('v_d = %s' % v_d)
                        for vo in DVolume.objects.filter(container=co):
                            if (vo.dest_dir not in v_d):
                                vo.delete()

                        if ('opts' in containers[c]):
                            options = containers[c]['opts']
                            id_l = []
                            for o in options:
                                try:
                                    oo = ContainerOption.objects.get(container=co, name=o[0], val=o[1])
                                    id_l.append(oo.id)
                                except ContainerOption.DoesNotExist:
                                    oo = ContainerOption(container=co, name=o[0], val=o[1])
                                    oo.save()
                                    id_l.append(oo.id)
                            for oo in ContainerOption.objects.filter(container=co):
                                if (oo.id not in id_l):
                                    oo.delete()

                    if ('container_links' in r_d):
                        l_d = r_d['container_links']
                        for cname in l_d.keys():
                            ll = l_d[cname]
                            lsources = [l['source_container'] for l in ll]
                            co = DContainer.objects.get(rockon=ro, name=cname)
                            for clo in co.destination_container.all():
                                if (clo.name not in lsources):
                                    clo.delete()
                            for cl_d in ll:
                                sco = DContainer.objects.get(rockon=ro, name=cl_d['source_container'])
                                if (DContainerLink.objects.filter(source=sco, destination=co).exists()):
                                    clo = DContainerLink.objects.get(source=sco)
                                    clo.name = cl_d['name']
                                    clo.save()
                                else:
                                    clo = DContainerLink(source=sco,
                                                         destination=co, name=cl_d['name'])
                                    clo.save()

                    if ('custom_config' in r_d):
                        cc_d = r_d['custom_config']
                        for k in cc_d:
                            ccc_d = cc_d[k]
                            cco, created = DCustomConfig.objects.get_or_create(
                                rockon=ro, key=k,
                                defaults={'description': ccc_d['description'], 'label': ccc_d['label']})
                            if (not created):
                                cco.description = ccc_d['description']
                                cco.label = ccc_d['label']
                            if (not created and k == 'iprange' and ro.name == 'Plex'):
                                from storageadmin.models import NetworkInterface
                                try:
                                    ni = NetworkInterface.objects.filter(itype='management')[0]
                                    cco.val = ('%s/255.255.255.0' % ni.ipaddr)
                                except:
                                    pass
                            cco.save()
                    else:
                        cc_d = {}
                    for cco in DCustomConfig.objects.filter(rockon=ro):
                        if (cco.key not in cc_d):
                            cco.delete()
            return Response()

    def _get_available(self, request):
        msg = ('Network error while checking for updates. '
               'Please try again later.')
        with self._handle_exception(request, msg=msg):
            #r = requests.get('http://rockstor.com/rockons.json')
            #rockons = r.json()
            from rockon_json import rockons
            return rockons

    @transaction.atomic
    def delete(self, request, sname):
        with self._handle_exception(request):
            return Response()
