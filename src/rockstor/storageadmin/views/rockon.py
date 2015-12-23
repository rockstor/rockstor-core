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

import os
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
from django.conf import settings
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

    def post(self, request, command=None):
        with self._handle_exception(request):
            if (command == 'update'):
                rockons = self._get_available(request)
                for r in rockons:
                    try:
                        self._create_update_meta(r, rockons[r])
                    except Exception, e:
                        logger.error('Exception while processing rockon(%s) '
                                     'metadata: %s' % (r, e.__str__()))
            return Response()

    @transaction.atomic
    def _create_update_meta(self, name, r_d):
        ro_defaults = {'description': r_d['description'],
                       'website': r_d['website'],
                       'version': '1.0',
                       'state': 'available',
                       'status': 'stopped'}
        ro, created = RockOn.objects.get_or_create(name=name,
                                                   defaults=ro_defaults)
        if (not created):
            ro.description = ro_defaults['description']
            ro.website = ro_defaults['website']
            ro.version = ro_defaults['version']
        if ('ui' in r_d):
            ui_d = r_d['ui']
            ro.link = ui_d['slug']
            if ('https' in ui_d):
                ro.https = ui_d['https']
        if ('icon' in r_d):
            ro.icon = r_d['icon']
        if ('volume_add_support' in r_d):
            ro.volume_add_support = r_d['volume_add_support']
        if ('more_info' in r_d):
            ro.more_info = r_d['more_info']
        ro.save()
        containers = r_d['containers']
        for c in containers:
            c_d = containers[c]
            io, created = DImage.objects.get_or_create(name=c_d['image'],
                                                       defaults={'tag': 'latest',
                                                                 'repo': 'na'})
            co_defaults = {'rockon': ro,
                           'dimage': io,
                           'launch_order': c_d['launch_order'],}
            co, created = DContainer.objects.get_or_create(name=c,
                                                           defaults=co_defaults)
            if (co.rockon.name != ro.name):
                e_msg = ('Container(%s) belongs to another '
                         'Rock-On(%s). Update rolled back.' %
                         (c, co.rockon.name))
                handle_exception(Exception(e_msg), request)
            if (not created):
                co.dimage = io
                co.launch_order = co_defaults['launch_order']
            co.save()

            ports = {}
            if ('ports' in containers[c]):
                ports = containers[c]['ports']
                for p in ports:
                    p_d = ports[p]
                    if ('protocol' not in p_d):
                        p_d['protocol'] = None
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
            ports = [int(p) for p in ports]
            for po in DPort.objects.filter(container=co):
                if (po.containerp not in ports):
                    po.delete()

            v_d = {}
            if ('volumes' in c_d):
                v_d = c_d['volumes']
                for v in v_d:
                    cv_d = v_d[v]
                    vo_defaults = {'description': cv_d['description'],
                                   'label': cv_d['label']}
                    vo, created = DVolume.objects.get_or_create(dest_dir=v, container=co,
                                                                defaults=vo_defaults)
                    if (not created):
                        vo.description = vo_defaults['description']
                        vo.label = vo_defaults['label']
                    if ('min_size' in cv_d):
                        vo.min_size = cv_d['min_size']
                    vo.save()
            for vo in DVolume.objects.filter(container=co):
                if (vo.dest_dir not in v_d):
                    vo.delete()

            if ('opts' in containers[c]):
                options = containers[c]['opts']
                id_l = []
                for o in options:
                    #there are no unique constraints on this model, so we need this bandaid.
                    if (ContainerOption.objects.filter(container=co, name=o[0], val=o[1]).count() > 1):
                        ContainerOption.objects.filter(container=co, name=o[0], val=o[1]).delete()
                    oo, created = ContainerOption.objects.get_or_create(container=co,
                                                                        name=o[0],
                                                                        val=o[1])
                    id_l.append(oo.id)
                for oo in ContainerOption.objects.filter(container=co):
                    if (oo.id not in id_l):
                        oo.delete()

        if ('container_links' in r_d):
            l_d = r_d['container_links']
            for cname in l_d:
                ll = l_d[cname]
                lsources = [l['source_container'] for l in ll]
                co = DContainer.objects.get(rockon=ro, name=cname)
                for clo in co.destination_container.all():
                    if (clo.name not in lsources):
                        clo.delete()
                for cl_d in ll:
                    sco = DContainer.objects.get(rockon=ro, name=cl_d['source_container'])
                    clo, created = DContainerLink.objects.get_or_create(source=sco,
                                                                        destination=co)
                    clo.name = cl_d['name']
                    clo.save()

        cc_d = {}
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
                    cco.save()
        for cco in DCustomConfig.objects.filter(rockon=ro):
            if (cco.key not in cc_d):
                cco.delete()

    def _get_available(self, request):
        msg = ('Network error while checking for updates. '
               'Please try again later.')
        url_root = settings.ROCKONS.get('remote_metastore')
        with self._handle_exception(request, msg=msg):
            response = requests.get(url_root, timeout=10)
            root = response.json()
            meta_cfg = {}
            for k,v in root.items():
                cur_meta_url = '%s/%s' % (url_root, v)
                try:
                    cur_res = requests.get(cur_meta_url, timeout=10)
                    logger.debug('meta_cfg updated for %s' % k)
                    meta_cfg.update(cur_res.json())
                except Exception, e:
                    logger.error('Error processing %s: %s' %
                                 (cur_meta_url, e.__str__()))
            local_root = settings.ROCKONS.get('local_metastore')
            for f in os.listdir(local_root):
                fp = '%s/%s' % (local_root, f)
                try:
                    with open(fp) as fo:
                        ds = json.load(fo)
                        meta_cfg.update(ds)
                except Exception, e:
                    logger.error('Error processing %s: %s' %
                                 (fp, e.__str__()))
            return meta_cfg




    @transaction.atomic
    def delete(self, request, sname):
        with self._handle_exception(request):
            return Response()
