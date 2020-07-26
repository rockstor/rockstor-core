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

import os
import re
from shutil import move
from tempfile import mkstemp
import psutil
from django.conf import settings
from system.osi import run_command
from storageadmin.models import DContainer, DVolume, DPort, DCustomConfig
from fs.btrfs import mount_share
from system.pkg_mgmt import install_pkg
from rockon_utils import container_status


def discourse_repo(rockon):
    co = DContainer.objects.get(rockon=rockon)
    vo = DVolume.objects.get(container=co)
    share_mnt = "%s%s" % (settings.MNT_PT, vo.share.name)
    mount_share(vo.share, share_mnt)
    return "%s/%s" % (share_mnt, rockon.name.lower())


def discourse_install(rockon):
    # 1. install git
    git = "/usr/bin/git"
    if not os.path.isfile(git):
        install_pkg("git")

    # 2. prep Discourse.yml
    repo = discourse_repo(rockon)
    if not os.path.isdir(repo):
        run_command(
            [git, "clone", "https://github.com/discourse/discourse_docker.git", repo]
        )

    co = DContainer.objects.get(rockon=rockon)
    po = DPort.objects.get(container=co)
    cc_map = {}
    for cco in DCustomConfig.objects.filter(rockon=rockon):
        cc_map[cco.key] = cco.val
    mem = int((psutil.virtual_memory().total / (1024 * 1024)) * 0.25)

    fo, npath = mkstemp()
    src_yml = "%s/samples/standalone.yml" % repo
    dst_yml = "%s/containers/%s.yml" % (repo, rockon.name.lower())
    with open(src_yml) as sfo, open(npath, "w") as tfo:
        for line in sfo.readlines():
            if re.match('  - "80:80"', line) is not None:
                tfo.write('  - "%d:80"\n' % po.hostp)
            elif re.match("  #db_shared_buffers:", line) is not None:
                tfo.write('  db_shared_buffers: "%dMB"\n' % mem)
            elif re.match("  #UNICORN_WORKERS:", line) is not None:
                tfo.write("  UNICORN_WORKERS: 3\n")
            elif re.match("  DISCOURSE_DEVELOPER_EMAILS:", line) is not None:
                tfo.write(
                    "  DISCOURSE_DEVELOPER_EMAILS: '%s'\n" % cc_map["admin-email"]
                )
            elif re.match("  DISCOURSE_HOSTNAME:", line) is not None:
                tfo.write("  DISCOURSE_HOSTNAME: '%s'\n" % cc_map["hostname"])
            elif re.match("  DISCOURSE_SMTP_ADDRESS:", line) is not None:
                tfo.write("  DISCOURSE_SMTP_ADDRESS: %s\n" % cc_map["smtp-address"])
            elif re.match("  #DISCOURSE_SMTP_PORT:", line) is not None:
                tfo.write("  DISCOURSE_SMTP_PORT: %s\n" % cc_map["smtp-port"])
            elif re.match("  #DISCOURSE_SMTP_USER_NAME:", line) is not None:
                tfo.write("  DISCOURSE_SMTP_USER_NAME: %s\n" % cc_map["smtp-username"])
            elif re.match("  #DISCOURSE_SMTP_PASSWORD:", line) is not None:
                tfo.write("  DISCOURSE_SMTP_PASSWORD: %s\n" % cc_map["smtp-password"])
            elif (
                re.match("      host: /var/discourse/shared/standalone", line)
                is not None
            ):  # noqa E501
                tfo.write("      host: %s/shares/standalone\n" % repo)
            elif (
                re.match(
                    "      host: /var/discourse/shared/standalone/log/var-log", line
                )
                is not None
            ):  # noqa E501
                tfo.write("      host: %s/shared/standalone/log/var-log\n" % repo)
            else:
                tfo.write(line)
    move(npath, dst_yml)

    # 3. bootstrap: launcher bootstrap app
    run_command(["%s/launcher" % repo, "bootstrap", rockon.name.lower()])

    # 4. start: launcher start app
    run_command(["%s/launcher" % repo, "start", rockon.name.lower()])


def discourse_uninstall(rockon):
    repo = discourse_repo(rockon)
    if os.path.isdir(repo):
        run_command(["%s/launcher" % repo, "destroy", rockon.name.lower()])
    return run_command(["/usr/bin/rm", "-rf", repo])


def discourse_stop(rockon):
    repo = discourse_repo(rockon)
    return run_command(["%s/launcher" % repo, "stop", rockon.name.lower()])


def discourse_start(rockon):
    repo = discourse_repo(rockon)
    return run_command(["%s/launcher" % repo, "start", rockon.name.lower()])


def discourse_status(rockon):
    return container_status(rockon.name.lower())
