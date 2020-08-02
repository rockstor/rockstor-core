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

import json
import logging
import os
import pickle
import re

import requests
from django.conf import settings
from django.db import transaction
from django_ztask.models import Task
from rest_framework.response import Response

import rest_framework_custom as rfc
from rockon_helpers import docker_status, rockon_status
from smart_manager.models import Service
from storageadmin.models import (
    RockOn,
    DImage,
    DContainer,
    DPort,
    DVolume,
    ContainerOption,
    DCustomConfig,
    DContainerLink,
    DContainerEnv,
    DContainerDevice,
    DContainerArgs,
)
from storageadmin.serializers import RockOnSerializer
from storageadmin.util import handle_exception

logger = logging.getLogger(__name__)


class RockOnView(rfc.GenericView):
    serializer_class = RockOnSerializer

    @transaction.atomic
    def get_queryset(self, *args, **kwargs):
        if docker_status():
            pending_rids = {}
            failed_rids = {}
            for t in Task.objects.filter(
                function_name__regex="rockon_helpers"
            ):  # noqa E501
                rid = pickle.loads(t.args)[0]
                if t.retry_count == 0 and t.failed is not None:
                    failed_rids[rid] = t
                else:
                    pending_rids[rid] = t
            # Remove old failed attempts @todo: we should prune all failed
            # tasks of the past, not here though.
            for rid in pending_rids.keys():
                if rid in failed_rids:
                    pt = pending_rids[rid]
                    ft = failed_rids[rid]
                    if failed_rids[rid].created > pending_rids[rid].created:
                        # this should never be the case. pending tasks either
                        # succeed and get deleted or they are marked failed.
                        msg = (
                            "Found a failed Task ({}) in the future of a "
                            "pending Task ({})."
                        ).format(ft.uuid, pt.uuid)
                        handle_exception(Exception(msg), self.request)
                    failed_rids[rid].delete()
                    del failed_rids[rid]
            for ro in RockOn.objects.all():
                if ro.state == "installed":
                    # update current running status of installed rockons.
                    if ro.id not in pending_rids:
                        ro.status = rockon_status(ro.name)
                elif re.search("pending", ro.state) is not None:
                    if ro.id in failed_rids:
                        # we update the status on behalf of the task runner
                        func_name = t.function_name.split(".")[-1]
                        ro.state = "%s_failed" % func_name
                    elif ro.id not in pending_rids:
                        logger.error(
                            (
                                "Rockon ({}) is in pending state but "
                                "there is no pending or failed task "
                                "for it."
                            ).format(ro.name)
                        )
                        ro.state = "%s_failed" % ro.state.split("_")[1]
                    else:
                        logger.debug(
                            ("Rockon ({}) is in pending state.").format(ro.name)
                        )
                elif ro.state == "uninstall_failed":
                    ro.state = "installed"
                ro.save()
        return RockOn.objects.filter().order_by("name")

    @transaction.atomic
    def put(self, request):
        with self._handle_exception(request):
            return Response()

    def post(self, request, command=None):
        with self._handle_exception(request):
            if command == "update":
                logger.debug("Update Rock-ons info in database")
                rockons = self._get_available()
                # Delete metadata for apps no longer in metastores.
                self._delete_deprecated(rockons)

                error_str = ""
                for r in rockons:
                    try:
                        self._create_update_meta(r, rockons[r])
                    except Exception as e:
                        error_str = "%s: %s" % (r, e.__str__())
                        logger.exception(e)
                if len(error_str) > 0:
                    e_msg = (
                        "Errors occurred while processing updates for "
                        "the following Rock-ons ({})."
                    ).format(error_str)
                    handle_exception(Exception(e_msg), request)
            return Response()

    @transaction.atomic
    def _delete_deprecated(self, rockons):
        cur_rockons = [
            ro.name
            for ro in RockOn.objects.filter(state__regex=r"available|install_failed")
        ]
        for cr in cur_rockons:
            if cr not in rockons:
                RockOn.objects.get(name=cr).delete()

    @staticmethod
    def _next_available_default_hostp(port):
        while True:
            if DPort.objects.filter(hostp=port).exists():
                port += 1
            else:
                return port

    @transaction.atomic
    def _create_update_meta(self, name, r_d):
        # Update our application state with any changes from hosted app
        # profiles(app.json files). Some attributes cannot be updated if the
        # Rock-on is currently installed. These will be logged and ignored.
        ro_defaults = {
            "description": r_d["description"],
            "website": r_d["website"],
            "version": r_d["version"],
            "state": "available",
            "status": "stopped",
        }
        ro, created = RockOn.objects.get_or_create(name=name, defaults=ro_defaults)
        if not created:
            ro.description = ro_defaults["description"]
            ro.website = ro_defaults["website"]
            ro.version = ro_defaults["version"]
        if "ui" in r_d:
            ui_d = r_d["ui"]
            ro.link = ui_d["slug"]
            if "https" in ui_d:
                ro.https = ui_d["https"]
        if "icon" in r_d:
            ro.icon = r_d["icon"]
        if "volume_add_support" in r_d:
            ro.volume_add_support = r_d["volume_add_support"]
        if "more_info" in r_d:
            ro.more_info = r_d["more_info"]
        ro.save()

        containers = r_d["containers"]
        cur_containers = [co.name for co in DContainer.objects.filter(rockon=ro)]
        if len(set(containers.keys()) ^ set(cur_containers)) != 0:
            if ro.state not in ("available", "install_failed"):
                e_msg = (
                    "Cannot add/remove container definitions for {} as "
                    "it is not in available state. Uninstall the "
                    "Rock-on first and try again."
                ).format(ro.name)
                handle_exception(Exception(e_msg), self.request)
            # rock-on is in available state. we can safely wipe metadata
            # and start fresh.
            DContainer.objects.filter(rockon=ro).delete()

        for c in containers:
            c_d = containers[c]
            co = None
            if DContainer.objects.filter(name=c).exists():
                co = DContainer.objects.get(name=c)
                if co.rockon.id != ro.id:
                    e_msg = (
                        "Duplicate container ({}) definition detected. "
                        "It belongs to another Rock-on ({}). Uninstall "
                        "one of them and "
                        "try again."
                    ).format(co.name, co.rockon.name)
                    handle_exception(Exception(e_msg), self.request)

                if co.dimage.name != c_d["image"]:
                    if ro.state not in ("available", "install_failed"):
                        e_msg = (
                            "Cannot change image of the container ({}) "
                            "as it belongs to an installed Rock-on ({}). "
                            "Uninstall it first and "
                            "try again."
                        ).format(co.name, ro.name)
                        handle_exception(Exception(e_msg), self.request)
                    co.dimage.delete()
            if co is None:
                co = DContainer(name=c, rockon=ro)
            defaults = {
                "repo": "na",
            }
            io, created = DImage.objects.get_or_create(
                name=c_d["image"], tag=c_d.get("tag", "latest"), defaults=defaults
            )
            co.dimage = io
            co.launch_order = c_d["launch_order"]
            if "uid" in c_d:
                co.uid = int(c_d["uid"])
            co.save()

            ports = containers[c].get("ports", {})
            cur_ports = [po.containerp for po in DPort.objects.filter(container=co)]
            if len(set(map(int, ports.keys())) ^ set(cur_ports)) != 0:
                if ro.state not in ("available", "install_failed"):
                    e_msg = (
                        "Cannot add/remove port definitions of the "
                        "container ({}) as it belongs to an installed "
                        "Rock-on ({}). Uninstall it first and "
                        "try again."
                    ).format(co.name, ro.name)
                    handle_exception(Exception(e_msg), self.request)
                DPort.objects.filter(container=co).delete()

            for p in ports:
                p_d = ports[p]
                if "protocol" not in p_d:
                    p_d["protocol"] = None
                p = int(p)
                po = None
                if DPort.objects.filter(containerp=p, container=co).exists():
                    po = DPort.objects.get(containerp=p, container=co)
                    if po.hostp_default != p_d["host_default"]:
                        po.hostp_default = self._next_available_default_hostp(
                            p_d["host_default"]
                        )
                    po.description = p_d["description"]
                    po.protocol = p_d["protocol"]
                    po.label = p_d["label"]
                else:
                    # let's find next available default if default is already
                    # taken
                    def_hostp = self._next_available_default_hostp(
                        p_d["host_default"]
                    )  # noqa E501
                    po = DPort(
                        description=p_d["description"],
                        hostp=def_hostp,
                        containerp=p,
                        hostp_default=def_hostp,
                        container=co,
                        protocol=p_d["protocol"],
                        label=p_d["label"],
                    )
                if "ui" in p_d:
                    po.uiport = p_d["ui"]
                if po.uiport:
                    ro.ui = True
                    ro.save()
                po.save()

            v_d = c_d.get("volumes", {})
            cur_vols = [vo.dest_dir for vo in DVolume.objects.filter(container=co)]
            # cur_vols can have entries not in the config for Shares mapped
            # post install.  If we have more volumes defined in the rock-on
            # definition than we have previously seen for this rockon, ie
            # volumes added in newer definition, then remove our existing
            # volumes record.
            if len(set(v_d.keys()) - set(cur_vols)) != 0:
                # but only if the current state is 'available' (to install) or
                # 'install failed', otherwise raise warning about changing an
                # installed rock-ons.
                if ro.state not in ("available", "install_failed"):
                    e_msg = (
                        "Cannot add/remove volume definitions of the "
                        "container ({}) as it belongs to an installed "
                        "Rock-on ({}). Uninstall it first and "
                        "try again."
                    ).format(co.name, ro.name)
                    handle_exception(Exception(e_msg), self.request)
                # Delete all volume entries for this container so that they
                # might be created a fresh.
                DVolume.objects.filter(container=co).delete()
            # If the existing rock-on db entry indicates this container is not
            # installed ie state available or install_failed then check if we
            # need to remove any now deprecated volume entries.
            # Ie updated config that has removed a previously seen volume.
            if ro.state in ("available", "install_failed"):
                if len(set(cur_vols) - set(v_d.keys())) > 0:
                    # we have some current volumes in db that are no longer in
                    # our updated rock-on definition so remove all volumes for
                    # this rock-on so they might be updated whole sale.
                    # Delete all volume entries for this container so that they
                    # might be created a fresh.
                    DVolume.objects.filter(container=co).delete()

            # Cycle through all volumes in the rock-on json definition and
            # update or create the appropriate db volumes entry.
            for v in v_d:
                cv_d = v_d[v]
                vo_defaults = {
                    "description": cv_d["description"],
                    "label": cv_d["label"],
                }

                vo, created = DVolume.objects.get_or_create(
                    dest_dir=v, container=co, defaults=vo_defaults
                )
                # If this db entry previously existed then update its
                # description and label to that found in our rock-on json
                # This ensures changes made in repo json to the description and
                # label's get updated in the local db.
                if not created:
                    vo.description = vo_defaults["description"]
                    vo.label = vo_defaults["label"]
                if "min_size" in cv_d:
                    vo.min_size = cv_d["min_size"]
                vo.save()

            self._update_env(co, c_d)
            self._update_device(co, c_d)
            options = containers[c].get("opts", [])
            id_l = []
            for o in options:
                # there are no unique constraints on this model, so we need
                # this bandaid.
                if (
                    ContainerOption.objects.filter(
                        container=co, name=o[0], val=o[1]
                    ).count()
                    > 1
                ):
                    ContainerOption.objects.filter(
                        container=co, name=o[0], val=o[1]
                    ).delete()
                oo, created = ContainerOption.objects.get_or_create(
                    container=co, name=o[0], val=o[1]
                )
                id_l.append(oo.id)
            for oo in ContainerOption.objects.filter(container=co):
                if oo.id not in id_l:
                    oo.delete()

            cmd_args = containers[c].get("cmd_arguments", [])
            id_l = []
            for ca in cmd_args:
                # there are no unique constraints on this model, so we need
                # this bandaid.
                if (
                    DContainerArgs.objects.filter(
                        container=co, name=ca[0], val=ca[1]
                    ).count()
                    > 1
                ):
                    DContainerArgs.objects.filter(
                        container=co, name=ca[0], val=ca[1]
                    ).delete()
                cao, created = DContainerArgs.objects.get_or_create(
                    container=co, name=ca[0], val=ca[1]
                )
                id_l.append(cao.id)
            for cao in DContainerArgs.objects.filter(container=co):
                if cao.id not in id_l:
                    cao.delete()

        l_d = r_d.get("container_links", {})
        for cname in l_d:
            ll = l_d[cname]
            lsources = [l["source_container"] for l in ll]
            co = DContainer.objects.get(rockon=ro, name=cname)
            for clo in co.destination_container.all():
                if clo.name not in lsources:
                    clo.delete()
            for cl_d in ll:
                sco = DContainer.objects.get(rockon=ro, name=cl_d["source_container"])
                clo, created = DContainerLink.objects.get_or_create(
                    source=sco, destination=co
                )
                clo.name = cl_d["name"]
                clo.save()
        self._update_cc(ro, r_d)

    def _sorted_keys(self, cd):
        sorted_keys = [""] * len(cd.keys())
        for k in cd:
            ccd = cd[k]
            idx = ccd.get("index", 0)
            if idx == 0:
                for i in range(len(sorted_keys)):
                    if sorted_keys[i] == "":
                        sorted_keys[i] = k
                        break
            else:
                sorted_keys[idx - 1] = k
        return sorted_keys

    def _update_model(self, modelinst, ad):
        for k, v in ad.iteritems():
            setattr(modelinst, k, v)
        modelinst.save()

    def _update_cc(self, ro, r_d):
        cc_d = r_d.get("custom_config", {})
        for k in self._sorted_keys(cc_d):
            ccc_d = cc_d[k]
            defaults = {
                "description": ccc_d["description"],
                "label": ccc_d["label"],
            }
            cco, created = DCustomConfig.objects.get_or_create(
                rockon=ro, key=k, defaults=defaults
            )
            if not created:
                self._update_model(cco, defaults)
        for cco in DCustomConfig.objects.filter(rockon=ro):
            if cco.key not in cc_d:
                cco.delete()

    def _update_device(self, co, c_d):
        cd_d = c_d.get("devices", {})
        for d in cd_d:
            ccd_d = cd_d[d]
            defaults = {
                "description": ccd_d["description"],
                "label": ccd_d["label"],
            }
            cd, created = DContainerDevice.objects.get_or_create(
                container=co, dev=d, defaults=defaults
            )
            if not created:
                self._update_model(cd, defaults)

    def _update_env(self, co, c_d):
        cc_d = c_d.get("environment", {})
        for k in self._sorted_keys(cc_d):
            ccc_d = cc_d[k]
            defaults = {
                "description": ccc_d["description"],
                "label": ccc_d["label"],
            }
            cco, created = DContainerEnv.objects.get_or_create(
                container=co, key=k, defaults=defaults
            )
            if not created:
                self._update_model(cco, defaults)
        for eo in DContainerEnv.objects.filter(container=co):
            if eo.key not in cc_d:
                eo.delete()

    def _get_available(self):
        if Service.objects.get(name="docker").config is None:
            # don't fetch if service is not configured.
            return {}

        url_root = settings.ROCKONS.get("remote_metastore")
        remote_root = "%s/%s" % (url_root, settings.ROCKONS.get("remote_root"))
        msg = ("Error while processing remote metastore at ({}).").format(remote_root)
        with self._handle_exception(self.request, msg=msg):
            response = requests.get(remote_root, timeout=10)
            if response.status_code != 200:
                response.raise_for_status()
            root = response.json()

        meta_cfg = {}
        for k, v in root.items():
            cur_meta_url = "%s/%s" % (url_root, v)
            msg = ("Error while processing Rock-on profile at ({}).").format(
                cur_meta_url
            )
            with self._handle_exception(self.request, msg=msg):
                cur_res = requests.get(cur_meta_url, timeout=10)
                if cur_res.status_code != 200:
                    cur_res.raise_for_status()
                meta_cfg.update(cur_res.json())

        local_root = settings.ROCKONS.get("local_metastore")
        if os.path.isdir(local_root):
            for f in os.listdir(local_root):
                fp = "%s/%s" % (local_root, f)
                msg = ("Error while processing Rock-on profile at ({}).").format(fp)
                with self._handle_exception(self.request, msg=msg):
                    with open(fp) as fo:
                        ds = json.load(fo)
                        meta_cfg.update(ds)
        return meta_cfg

    @transaction.atomic
    def delete(self, request, sname):
        with self._handle_exception(request):
            return Response()
