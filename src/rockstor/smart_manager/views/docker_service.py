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
import re
import shutil

import distro
from django.conf import settings
from django.db import transaction
from rest_framework.response import Response

from base_service import BaseServiceDetailView
from fs.btrfs import mount_share
from smart_manager.models import Service
from storageadmin.models import Share
from storageadmin.util import handle_exception
from system.services import systemctl

logger = logging.getLogger(__name__)

DOCKERD = "/usr/bin/dockerd"

# Distro's for which we have known working conf/docker-distroid.service files.
KNOWN_DISTRO_IDS = ["rockstor", "opensuse-leap", "opensuse-tumbleweed"]


class DockerServiceView(BaseServiceDetailView):
    name = "docker"

    def _validate_root(self, request, root):
        try:
            return Share.objects.get(name=root)
        except Exception as e:
            logger.exception(e)
            e_msg = "Share name ({}) does not exist.".format(root)
            handle_exception(Exception(e_msg), request)

    @transaction.atomic
    def post(self, request, command):
        service = Service.objects.get(name=self.name)

        if command == "config":
            config = request.data.get("config", None)
            root_share = config["root_share"]
            self._validate_root(request, root_share)
            self._save_config(service, config)

        elif command == "start":
            try:
                config = self._get_config(service)
            except Exception as e:
                logger.exception(e)
                e_msg = (
                    "Cannot start without configuration. "
                    "Please configure (System->Services) and try again."
                )
                handle_exception(Exception(e_msg), request)

            share = self._validate_root(request, config["root_share"])
            mnt_pt = "{}{}".format(settings.MNT_PT, share.name)
            if not share.is_mounted:
                mount_share(share, mnt_pt)

            distro_id = distro.id()  # for Leap 15 <--> Tumbleweed moves.
            if distro_id not in KNOWN_DISTRO_IDS:
                distro_id = "generic"

            # Write a custom daemon.json file (openSUSE only)
            conf_file = "{}/docker-daemon.json".format(settings.CONFROOT)
            if re.match("opensuse", distro_id) is not None:
                # Write them to file
                self._write_docker_daemon_conf(conf_file, mnt_pt, request)

            # Then write the docker.service file
            try:
                self._write_docker_service(distro_id, mnt_pt, conf_file)
            except Exception as e:
                logger.exception(e)
                e_msg = "An error occurred while writing the docker.service file"
                handle_exception(Exception(e_msg), request)

            if distro_id == "rockstor":
                socket_file = "{}/docker.socket".format(settings.CONFROOT)
                shutil.copy(socket_file, "/etc/systemd/system/docker.socket")
            systemctl(self.name, "enable")
            systemctl(self.name, "start")
        elif command == "stop":
            systemctl(self.name, "stop")
            systemctl(self.name, "disable")
        return Response()

    def _write_docker_daemon_conf(self, outf, data_root, request):
        """
        Takes the default daemon.json from package and replace or add options
        with Rockstor's customizations.
        :param outf: string. path to output json conf file
        :param data_root: path to rockons-root
        :param request:
        """
        inf = "/etc/docker/daemon.json"
        try:
            with open(inf, "r") as f:
                dconf = json.load(f)
        except IOError as e:
            # If default conf cannot be loaded, create a new one:
            dconf = {}
        # define options
        dconf["data-root"] = data_root
        dconf["storage-driver"] = "btrfs"
        dconf["storage-opts"] = ["btrfs.min_space=1G"]
        dconf["log-driver"] = "journald"
        dconf["log-opts"] = {"tag": "{{.ImageName}}/{{.Name}}"}

        try:
            with open(outf, "w") as f:
                json.dump(dconf, f, indent=2, sort_keys=True)
                f.write("\n")
        except IOError as e:
            logger.exception(e)
            e_msg = "The dockerd configuration file couldn't be written to disk at {}.".format(
                outf
            )
            handle_exception(IOError(e_msg), request)

    def _write_docker_service(self, distro_id, mnt_pt, conf_file):
        docker_wrapper = "{}bin/docker-wrapper".format(settings.ROOT_DIR)
        # If openSUSE, source conf file from docker package itself
        if re.match("opensuse", distro_id) is not None:
            inf = "/usr/lib/systemd/system/docker.service"
        else:
            inf = "{}/docker-{}.service".format(settings.CONFROOT, distro_id)
        outf = "/etc/systemd/system/docker.service"
        with open(inf) as ino, open(outf, "w") as outo:
            for l in ino.readlines():
                if re.match("ExecStart=", l) is not None:
                    if re.match("opensuse", distro_id) is not None:
                        # point to config file written by _write_docker_daemon_conf()
                        outo.write("{} --config-file {}\n".format(l.strip(), conf_file))
                    else:
                        outo.write(
                            "{} {}\n".format(
                                l.strip().replace(DOCKERD, docker_wrapper, 1), mnt_pt
                            )
                        )
                elif re.match("Type=notify", l) is not None:
                    # Our docker wrapper use need NotifyAccess=all: avoids
                    # "Got notification message from PID ####1, but
                    # reception only permitted for main PID ####2"
                    outo.write(l)
                    outo.write("NotifyAccess=all\n")
                elif re.match("After=", l) is not None:
                    outo.write(
                        "{} {}\n".format(l.strip(), "rockstor-bootstrap.service")
                    )
                else:
                    outo.write(l)
