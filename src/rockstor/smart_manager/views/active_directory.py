"""
Copyright (c) 2012-2021 RockStor, Inc. <http://rockstor.com>
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
import socket

from django.db import transaction
from rest_framework.response import Response

from smart_manager.views.base_service import BaseServiceDetailView
from smart_manager.models import Service
from storageadmin.util import handle_exception
from system.directory_services import (
    update_nss,
    sssd_update_ad,
    join_domain,
    domain_workgroup,
    leave_domain,
    sssd_update_services,
)
from system.osi import run_command
from system.samba import update_global_config
from system.services import systemctl

logger = logging.getLogger(__name__)
REALM = "/usr/sbin/realm"


class ActiveDirectoryServiceView(BaseServiceDetailView):
    def _ntp_check(self, request):
        ntpo = Service.objects.get(name="ntpd")
        if not self._get_status(ntpo):
            e_msg = (
                "NTP must be configured and running first before Rockstor"
                " can join AD. Configure NTP service first "
                "and try again."
            )
            handle_exception(Exception(e_msg), request)

    @staticmethod
    def _resolve_check(domain, request):
        try:
            socket.gethostbyname(domain)
        except Exception as e:
            e_msg = (
                "Domain/Realm({}) could not be resolved. Check "
                "your DNS configuration and try again. "
                "Lower level error: {}".format(domain, e.__str__())
            )
            handle_exception(Exception(e_msg), request)

    @staticmethod
    def _validate_config(config, request):
        e_msg = None
        if "domain" not in config:
            e_msg = "Domain/Realm is required but missing in the input."
        elif "username" not in config:
            e_msg = "Administrator username is required but missing in the input"
        elif "password" not in config:
            e_msg = "Administrator password is required but missing in the input"
        if e_msg is not None:
            handle_exception(Exception(e_msg), request)

    def _config(self, service, request):
        try:
            return self._get_config(service)
        except Exception as e:
            e_msg = (
                "Missing configuration. Please configure the "
                "service and try again. Exception: {}".format(e.__str__())
            )
            handle_exception(Exception(e_msg), request)

    @transaction.atomic
    def post(self, request, command):

        with self._handle_exception(request):
            method = "sssd"
            service = Service.objects.get(name="active-directory")
            if command == "config":
                config = request.data.get("config")
                self._validate_config(config, request)

                # 1. Name resolution check
                self._resolve_check(config.get("domain"), request)

                # 2. realm discover check?
                domain = config.get("domain")
                try:
                    cmd = [REALM, "discover", "--name-only", domain]
                    o, e, rc = run_command(cmd)
                except Exception as e:
                    e_msg = (
                        "Failed to discover the given({}) AD domain. "
                        "Error: {}".format(domain, e.__str__())
                    )
                    handle_exception(Exception(e_msg), request)
                # Would be required only if method == "winbind":
                # validate_idmap_range(config)

                self._save_config(service, config)

            elif command == "start":
                config = self._config(service, request)
                domain = config.get("domain")
                # 1. make sure ntpd is running, or else, don't start.
                self._ntp_check(request)
                # 2. Name resolution check?
                self._resolve_check(config.get("domain"), request)

                if method == "winbind":
                    cmd = [
                        "/usr/sbin/authconfig",
                    ]
                    # nss
                    cmd += [
                        "--enablewinbind",
                        "--enablewins",
                    ]
                    # pam
                    cmd += [
                        "--enablewinbindauth",
                    ]
                    # smb
                    cmd += [
                        "--smbsecurity",
                        "ads",
                        "--smbrealm",
                        domain.upper(),
                    ]
                    # kerberos
                    cmd += [
                        "--krb5realm=%s" % domain.upper(),
                    ]
                    # winbind
                    cmd += [
                        "--enablewinbindoffline",
                        "--enablewinbindkrb5",
                        "--winbindtemplateshell=/bin/sh",
                    ]
                    # general
                    cmd += [
                        "--update",
                        "--enablelocauthorize",
                    ]
                    run_command(cmd)
                # 3. Get WORKGROUP from AD server
                config["workgroup"] = domain_workgroup(domain, method=method)

                # 4. Update Samba config
                smbo = Service.objects.get(name="smb")
                # smb_config = self._get_config(smbo)
                try:
                    smb_config = self._get_config(smbo)
                    if smb_config["workgroup"] != config["workgroup"]:
                        # the current Samba workgroup is different than what
                        # we need so stop here and alert the user
                        err_msg = (
                            "The AD domain workgroup differs from the workgroup "
                            "currently defined in the Samba configuration:\n"
                            "AD domain workgroup: {}\n"
                            "Samba workgroup: {}\n"
                            "Ensure the Samba workgroup matches the AD domain "
                            "workgroup and try again.".format(
                                config["workgroup"], smb_config["workgroup"]
                            )
                        )
                        raise Exception(err_msg)
                except TypeError:
                    # Samba service is not configured, so let's do that now
                    smb_config = {}
                    smb_config["workgroup"] = config["workgroup"]
                    self._save_config(smbo, smb_config)
                # finally:
                #     # Set Samba WORKGROUP as AD REALM and save entry to Model
                update_global_config(smb_config, config)

                # 5. Save final Active_Directory service config and join AD
                self._save_config(service, config)
                join_domain(config, method=method)

                # SSSD config
                # Ensure ifp service is activated
                sssd_update_services(service="ifp")
                # Customize domain settings
                if (
                    method == "sssd"
                    and (config.get("enumerate") or config.get("case_sensitive"))
                    is True
                ):
                    sssd_update_ad(domain, config)

                # Update nsswitch.conf
                update_nss(["passwd", "group"], "sss")

                systemctl("smb", "restart")
                systemctl("nmb", "restart")
                # The winbind service is required only for id mapping while
                # accessing samba shares hosted by Rockstor
                systemctl("winbind", "enable")
                systemctl("winbind", "start")

            elif command == "stop":
                config = self._config(service, request)
                try:
                    leave_domain(config, method=method)
                    smbo = Service.objects.get(name="smb")
                    smb_config = self._get_config(smbo)
                    update_global_config(smb_config)
                    systemctl("smb", "restart")
                    systemctl("nmb", "restart")
                    systemctl("winbind", "stop")
                    systemctl("winbind", "disable")
                    update_nss(["passwd", "group"], "sss", remove=True)
                except Exception as e:
                    e_msg = "Failed to leave AD domain({}). Error: {}".format(
                        config.get("domain"), e.__str__(),
                    )
                    handle_exception(Exception(e_msg), request)

            return Response()
