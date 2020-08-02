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

import re
import socket
from tempfile import mkstemp
import shutil
from rest_framework.response import Response
from storageadmin.util import handle_exception
from django.db import transaction
from base_service import BaseServiceDetailView
from smart_manager.models import Service
from system.osi import run_command
from system.samba import update_global_config
from system.services import systemctl

import logging

logger = logging.getLogger(__name__)
NET = "/usr/bin/net"


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
                "Domain/Realm(%s) could not be resolved. Check "
                "your DNS configuration and try again. "
                "Lower level error: %s" % (domain, e.__str__())
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

    @staticmethod
    def _join_domain(config, method="winbind"):
        domain = config.get("domain")
        admin = config.get("username")
        cmd = [NET, "ads", "join", "-U", admin]
        if method == "sssd":
            cmd = ["realm", "join", "-U", admin, domain]
        return run_command(cmd, input=("%s\n" % config.get("password")))

    @staticmethod
    def _domain_workgroup(domain=None, method="winbind"):
        cmd = [NET, "ads", "workgroup"]
        if method == "sssd":
            cmd = ["adcli", "info", domain]
        o, e, rc = run_command(cmd)
        match_str = "Workgroup:"
        if method == "sssd":
            match_str = "domain-short = "
        for l in o:
            l = l.strip()
            if re.match(match_str, l) is not None:
                return l.split(match_str)[1].strip()
        raise Exception(
            "Failed to retrieve Workgroup. out: %s err: %s rc: %d" % (o, e, rc)
        )

    @staticmethod
    def _update_sssd(domain):
        # add enumerate = True in sssd so user/group lists will be
        # visible on the web-ui.
        el = "enumerate = True\n"
        fh, npath = mkstemp()
        sssd_config = "/etc/sssd/sssd.conf"
        with open(sssd_config) as sfo, open(npath, "w") as tfo:
            domain_section = False
            for line in sfo.readlines():
                if domain_section is True:
                    if len(line.strip()) == 0 or line[0] == "[":
                        # empty line or new section without empty line before
                        # it.
                        tfo.write(el)
                        domain_section = False
                elif re.match("\[domain/%s]" % domain, line) is not None:
                    domain_section = True
                tfo.write(line)
            if domain_section is True:
                # reached end of file, also coinciding with end of domain
                # section
                tfo.write(el)
        shutil.move(npath, sssd_config)
        systemctl("sssd", "restart")

    @staticmethod
    def _leave_domain(config, method="winbind"):
        pstr = "%s\n" % config.get("password")
        cmd = [NET, "ads", "leave", "-U", config.get("username")]
        if method == "sssd":
            cmd = ["realm", "leave", config.get("domain")]
            return run_command(cmd)
        try:
            return run_command(cmd, input=pstr)
        except:
            status_cmd = [NET, "ads", "status", "-U", config.get("username")]
            o, e, rc = run_command(status_cmd, input=pstr, throw=False)
            if rc != 0:
                return logger.debug(
                    "Status shows not joined. out: %s err: %s rc: %d" % (o, e, rc)
                )
            raise

    def _config(self, service, request):
        try:
            return self._get_config(service)
        except Exception as e:
            e_msg = (
                "Missing configuration. Please configure the "
                "service and try again. Exception: %s" % e.__str__()
            )
            handle_exception(Exception(e_msg), request)

    @transaction.atomic
    def post(self, request, command):

        with self._handle_exception(request):
            method = "winbind"
            service = Service.objects.get(name="active-directory")
            if command == "config":
                config = request.data.get("config")
                self._validate_config(config, request)

                # 1. Name resolution check
                self._resolve_check(config.get("domain"), request)

                # 2. realm discover check?
                # @todo: phase our realm and just use net?
                domain = config.get("domain")
                try:
                    cmd = ["realm", "discover", "--name-only", domain]
                    o, e, rc = run_command(cmd)
                except Exception as e:
                    e_msg = (
                        "Failed to discover the given(%s) AD domain. "
                        "Error: %s" % (domain, e.__str__())
                    )
                    handle_exception(Exception(e_msg), request)

                default_range = "10000 - 999999"
                idmap_range = config.get("idmap_range", "10000 - 999999")
                idmap_range = idmap_range.strip()
                if len(idmap_range) > 0:
                    rfields = idmap_range.split()
                    if len(rfields) != 3:
                        raise Exception(
                            "Invalid idmap range. valid format is "
                            "two integers separated by a -. eg: "
                            "10000 - 999999"
                        )
                    try:
                        rlow = int(rfields[0].strip())
                        rhigh = int(rfields[2].strip())
                    except Exception as e:
                        raise Exception(
                            "Invalid idmap range. Numbers in the "
                            "range must be valid integers. "
                            "Error: %s." % e.__str__()
                        )
                    if rlow >= rhigh:
                        raise Exception(
                            "Invalid idmap range. Numbers in the "
                            "range must go from low to high. eg: "
                            "10000 - 999999"
                        )
                else:
                    config["idmap_range"] = default_range

                self._save_config(service, config)

            elif command == "start":
                config = self._config(service, request)
                smbo = Service.objects.get(name="smb")
                smb_config = self._get_config(smbo)
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
                config["workgroup"] = self._domain_workgroup(domain, method=method)
                self._save_config(service, config)
                update_global_config(smb_config, config)
                self._join_domain(config, method=method)
                if method == "sssd" and config.get("enumerate") is True:
                    self._update_sssd(domain)

                if method == "winbind":
                    systemctl("winbind", "enable")
                    systemctl("winbind", "start")
                systemctl("smb", "restart")
                systemctl("nmb", "restart")

            elif command == "stop":
                config = self._config(service, request)
                try:
                    self._leave_domain(config, method=method)
                    smbo = Service.objects.get(name="smb")
                    smb_config = self._get_config(smbo)
                    update_global_config(smb_config)
                    systemctl("smb", "restart")
                    systemctl("nmb", "restart")
                except Exception as e:
                    e_msg = "Failed to leave AD domain(%s). Error: %s" % (
                        config.get("domain"),
                        e.__str__(),
                    )
                    handle_exception(Exception(e_msg), request)

            return Response()
