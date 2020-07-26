"""
Copyright (c) 2012-2020 RockStor, Inc. <http://rockstor.com>
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

import logging
import time

from django.db import transaction
from rest_framework.response import Response

import rest_framework_custom as rfc
from rockon_helpers import docker_status, start, stop, install, uninstall, update
from storageadmin.models import (
    RockOn,
    DContainer,
    DVolume,
    DContainerDevice,
    Share,
    DPort,
    DCustomConfig,
    DContainerEnv,
    DContainerLabel,
)
from storageadmin.serializers import RockOnSerializer
from storageadmin.util import handle_exception
from system.services import superctl

logger = logging.getLogger(__name__)


class RockOnIdView(rfc.GenericView):
    serializer_class = RockOnSerializer

    def get_queryset(self, *args, **kwargs):
        return RockOn.objects.all()

    @staticmethod
    def _next_available_default_hostp(port):
        while True:
            if DPort.objects.filter(hostp=port).exists():
                port += 1
            else:
                return port

    @staticmethod
    def _pending_check(request):
        if RockOn.objects.filter(state__contains="pending").exists():
            e_msg = (
                "Another rock-on is in state transition. Multiple "
                "simultaneous Rock-on transitions are not "
                "supported. Please try again later."
            )
            handle_exception(Exception(e_msg), request)

    @transaction.atomic
    def post(self, request, rid, command):
        with self._handle_exception(request):

            if not docker_status():
                e_msg = "Docker service is not running. Start it and try again."
                handle_exception(Exception(e_msg), request)

            try:
                rockon = RockOn.objects.get(id=rid)
            except:
                e_msg = "Rock-on ({}) does not exist.".format(rid)
                handle_exception(Exception(e_msg), request)

            try:
                dname = "ztask-daemon"
                e_msg = "ztask daemon is not running and could not be started."
                o, e, rc = superctl(dname, "status")
                if rc == 1:
                    superctl(dname, "restart")
                    time.sleep(5)
            except Exception as e:
                logger.exception(e)
                handle_exception(Exception(e_msg), request)
            finally:
                if rc == 1:
                    o, e, rc = superctl(dname, "status")
                    if rc == 1:
                        handle_exception(Exception(e_msg), request)

            if command == "install":
                self._pending_check(request)
                share_map = request.data.get("shares", {})
                port_map = request.data.get("ports", {})
                dev_map = request.data.get("devices", {})
                cc_map = request.data.get("cc", {})
                env_map = request.data.get("environment", {})
                containers = DContainer.objects.filter(rockon=rockon)
                for co in containers:
                    for sname in share_map.keys():
                        dest_dir = share_map[sname]
                        if not Share.objects.filter(name=sname).exists():
                            e_msg = "Invalid share ({}).".format(sname)
                            handle_exception(Exception(e_msg), request)
                        if DVolume.objects.filter(
                            container=co, dest_dir=dest_dir
                        ).exists():
                            so = Share.objects.get(name=sname)
                            vo = DVolume.objects.get(container=co, dest_dir=dest_dir)
                            vo.share = so
                            vo.save()
                    # {'host_port' : 'container_port', ... }
                    for p in port_map.keys():
                        if DPort.objects.filter(hostp=p).exists():
                            dup_po = DPort.objects.get(hostp=p)
                            if dup_po.container.rockon.id != rockon.id:
                                if dup_po.container.rockon.state in (
                                    "installed",
                                    "pending_install",
                                ):
                                    # cannot claim from a rock-on that's
                                    # installed.
                                    conf_ro = dup_po.container.rockon.name
                                    e_msg = (
                                        "Port ({}) belongs to another "
                                        "rock-on ({}). Choose a different "
                                        "port. If you must choose the same "
                                        "port, uninstall ({}) first and try "
                                        "again."
                                    ).format(p, conf_ro, conf_ro)
                                    handle_exception(Exception(e_msg), request)
                                # change the host port to next available.
                                dup_po.hostp = self._next_available_default_hostp(
                                    dup_po.hostp
                                )  # noqa E501
                                dup_po.save()
                        for co2 in DContainer.objects.filter(rockon=rockon):
                            if DPort.objects.filter(
                                container=co2, containerp=port_map[p]
                            ).exists():
                                # found the container that needs this port.
                                po = DPort.objects.get(
                                    container=co2, containerp=port_map[p]
                                )
                                po.hostp = p
                                po.save()
                                break
                    for d in dev_map.keys():
                        if not DContainerDevice.objects.filter(
                            container=co, dev=d
                        ).exists():
                            e_msg = ("Invalid device variable ({}).").format(d)
                            handle_exception(Exception(e_msg), request)
                        cdo = DContainerDevice.objects.get(container=co, dev=d)
                        cdo.val = dev_map[d]
                        cdo.save()
                    for c in cc_map.keys():
                        if not DCustomConfig.objects.filter(
                            rockon=rockon, key=c
                        ).exists():
                            e_msg = "Invalid custom config key ({}).".format(c)
                            handle_exception(Exception(e_msg), request)
                        cco = DCustomConfig.objects.get(rockon=rockon, key=c)
                        cco.val = cc_map[c]
                        cco.save()
                    for e in env_map.keys():
                        if not DContainerEnv.objects.filter(
                            container=co, key=e
                        ).exists():
                            e_msg = ("Invalid environment variable ({}).").format(e)
                            handle_exception(Exception(e_msg), request)
                        ceo = DContainerEnv.objects.get(container=co, key=e)
                        ceo.val = env_map[e]
                        ceo.save()
                install.async(rockon.id)
                rockon.state = "pending_install"
                rockon.save()
            elif command == "uninstall":
                self._pending_check(request)
                if rockon.state != "installed":
                    e_msg = (
                        "Rock-on ({}) is not currently installed. Cannot "
                        "uninstall it."
                    ).format(rockon.name)
                    handle_exception(Exception(e_msg), request)
                if rockon.status == "started" or rockon.status == "pending_start":
                    e_msg = (
                        "Rock-on ({}) must be stopped before it can "
                        "be uninstalled. Stop it and "
                        "try again."
                    ).format(rockon.name)
                    handle_exception(Exception(e_msg), request)
                uninstall.async(rockon.id)
                rockon.state = "pending_uninstall"
                rockon.save()
                for co in DContainer.objects.filter(rockon=rockon):
                    DVolume.objects.filter(container=co, uservol=True).delete()
                    DContainerLabel.objects.filter(container=co).delete()
            elif command == "update":
                self._pending_check(request)
                if rockon.state != "installed":
                    e_msg = (
                        "Rock-on ({}) is not currently installed. Cannot update it."
                    ).format(rockon.name)
                    handle_exception(Exception(e_msg), request)
                if rockon.status == "started" or rockon.status == "pending_start":
                    e_msg = (
                        "Rock-on ({}) must be stopped before it can "
                        "be updated. Stop it and "
                        "try again."
                    ).format(rockon.name)
                    handle_exception(Exception(e_msg), request)
                share_map = request.data.get("shares")
                label_map = request.data.get("labels")
                if bool(share_map):
                    for co in DContainer.objects.filter(rockon=rockon):
                        for s in share_map.keys():
                            sname = share_map[s]
                            if not Share.objects.filter(name=sname).exists():
                                e_msg = "Invalid share ({}).".format(sname)
                                handle_exception(Exception(e_msg), request)
                            so = Share.objects.get(name=sname)
                            if DVolume.objects.filter(container=co, share=so).exists():
                                e_msg = (
                                    "Share ({}) is already assigned to this rock-on."
                                ).format(sname)
                                handle_exception(Exception(e_msg), request)
                            if DVolume.objects.filter(
                                container=co, dest_dir=s
                            ).exists():
                                e_msg = (
                                    "Directory ({}) is already mapped for "
                                    "this rock-on."
                                ).format(s)
                                handle_exception(Exception(e_msg), request)
                            if not s.startswith("/"):
                                e_msg = (
                                    "Invalid directory ({}). Must provide an "
                                    "absolute path. Eg: "
                                    "(/data/media)."
                                ).format(s)
                                handle_exception(Exception(e_msg), request)
                            do = DVolume(
                                container=co, share=so, uservol=True, dest_dir=s
                            )
                            do.save()
                if bool(label_map):
                    for co in DContainer.objects.filter(rockon=rockon):
                        for c in label_map.keys():
                            cname = label_map[c]
                            coname = co.name
                            if cname != coname:
                                continue
                            lo = DContainerLabel(container=co, key=cname, val=c)
                            lo.save()
                rockon.state = "pending_update"
                rockon.save()
                update.async(rockon.id)
            elif command == "stop":
                stop.async(rockon.id)
                rockon.status = "pending_stop"
                rockon.save()
            elif command == "start":
                start.async(rockon.id)
                rockon.status = "pending_start"
                rockon.save()
            elif command == "state_update":
                state = request.data.get("new_state")
                rockon.state = state
                rockon.save()
            elif command == "status_update":
                status = request.data.get("new_status")
                rockon.status = status
                rockon.save()
            return Response(RockOnSerializer(rockon).data)
