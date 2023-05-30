"""
Copyright (c) 2012-2023 Rockstor, Inc. <https://rockstor.com>
This file is part of Rockstor.

Rockstor is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

Rockstor is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
import collections
import logging
import os
import re
import platform
import shutil
import stat
from shutil import move, copy
from tempfile import mkstemp

import distro
from django.conf import settings

from system.osi import run_command
from system.constants import (
    MKDIR,
    MOUNT,
    USERMOD,
    SYSTEMCTL,
)

logger = logging.getLogger(__name__)

# Begin SFTP-related constants
SSHD_HEADER = "###BEGIN: Rockstor SFTP CONFIG. DO NOT EDIT BELOW THIS LINE###"
INTERNAL_SFTP_STR = "Subsystem\tsftp\tinternal-sftp"

# Named Tuple to define sshd files according to their purpose.
# sshd - rockstor-target for sshd config additions.
# sshd_os - OS default config file we may have to edit (see sftp-server disablement)
# sftp - rockstor-target for sftp config additions.
# AllowUsers - rockstor-target for AllowUsers config - NOT CURRENTLY IMPLEMENTED
sshd_files = collections.namedtuple("sshd_files", "sshd sshd_os sftp AllowUsers")

# Dict of sshd_files indexed by distro.id
SSHD_CONFIG = {
    # Account for distro 1.7.0 onwards reporting "opensuse" for id in opensuse-leap.
    "opensuse": sshd_files(
        sshd="/etc/ssh/sshd_config",
        sshd_os="/etc/ssh/sshd_config",
        sftp="/etc/ssh/sshd_config",
        AllowUsers="/etc/ssh/sshd_config",
    ),
    "opensuse-leap": sshd_files(
        sshd="/etc/ssh/sshd_config",
        sshd_os="/etc/ssh/sshd_config",
        sftp="/etc/ssh/sshd_config",
        AllowUsers="/etc/ssh/sshd_config",
    ),
    # Newer overload  - type files
    "opensuse-tumbleweed": sshd_files(
        sshd="/etc/ssh/sshd_config.d/rockstor-sshd.conf",
        sshd_os="/usr/etc/ssh/sshd_config",
        sftp="/etc/ssh/sshd_config.d/rockstor-sftp.conf",
        AllowUsers="/etc/ssh/sshd_config.d/rockstor-AllowUsers.conf",
    ),
}


def init_sftp_config(sshd_config=None):
    """
    Establish our default sftp configuration within the distro specific file
    or a file passed by full path.
    :param sshd_config:
    :return: True if file found and alterations were made, False otherwise.
    :rtype boolean:
    """
    if sshd_config is None:
        sshd_config = SSHD_CONFIG[distro.id()].sftp
    sshd_restart = False
    if not os.path.isfile(sshd_config):
        logger.info("SSHD - Creating new configuration file ({}).".format(sshd_config))
    # Set AllowUsers and Subsystem sftp-internal if not already in-place.
    # N.B. opening mode "a+" creates this file if it doesn't exist - rw either way.
    # Post Python 3, consider build-in open with custom opener.
    with os.fdopen(
        os.open(sshd_config, os.O_RDWR | os.O_CREAT, stat.S_IRUSR | stat.S_IWUSR), "a+"
    ) as sfo:
        found = False
        for line in sfo.readlines():
            if (
                re.match(SSHD_HEADER, line) is not None
                or re.match("AllowUsers ", line) is not None
                or re.match(INTERNAL_SFTP_STR, line) is not None
            ):
                found = True
                logger.info("SSHD ({}) already initialised".format(sshd_config))
                break
        if not found:
            sshd_restart = True
            sfo.write("{}\n".format(SSHD_HEADER))
            sfo.write("{}\n".format(INTERNAL_SFTP_STR))
            # TODO Split out AllowUsers into SSHD_CONFIG[distro.id()].AllowUsers
            if os.path.isfile("{}/{}".format(settings.CONFROOT, "PermitRootLogin")):
                sfo.write("AllowUsers root\n")
            logger.info("SSHD ({}) initialised".format(sshd_config))
    return sshd_restart


def update_sftp_user_share_config(input_map):
    """
    Receives sftp-related customization settings and writes them to SSHD_CONFIG.
    :param input_map: dictionary of user,directory pairs.
    :return:
    """
    fo, npath = mkstemp()
    # TODO: Split out AllowUsers into SSHD_CONFIG[distro.id()].AllowUsers
    userstr = "AllowUsers"
    if os.path.isfile("{}/{}".format(settings.CONFROOT, "PermitRootLogin")):
        userstr += " root {}".format(" ".join(input_map.keys()))
    else:
        userstr += " {}".format(" ".join(input_map.keys()))
    distro_id = distro.id()
    with open(SSHD_CONFIG[distro_id].sftp) as sfo, open(npath, "w") as tfo:
        for line in sfo.readlines():
            if re.match(SSHD_HEADER, line) is None:
                tfo.write(line)
            else:
                break
        tfo.write("{}\n".format(SSHD_HEADER))
        # Detect sftp service status and ensure we maintain it
        if is_sftp_running():
            tfo.write("{}\n".format(INTERNAL_SFTP_STR))
        tfo.write("{}\n".format(userstr))
        # Set options for each user according to openSUSE's defaults:
        # https://en.opensuse.org/SDB:SFTP_server_with_Chroot#Match_rule_block
        # TODO: implement webUI element to re-enable rsync over ssh by omitting
        #   the `ForceCommand internal-sftp` line below.
        for user in input_map:
            tfo.write("Match User {}\n".format(user))
            tfo.write("\tForceCommand internal-sftp\n")
            tfo.write("\tChrootDirectory {}\n".format(input_map[user]))
            tfo.write("\tX11Forwarding no\n")
            tfo.write("\tAllowTcpForwarding no\n")

    move(npath, SSHD_CONFIG[distro_id].sftp)
    try:
        run_command([SYSTEMCTL, "reload", "sshd"], log=True)
    except:
        return run_command([SYSTEMCTL, "restart", "sshd"], log=True)


def toggle_sftp_service(switch=True):
    """
    Toggles the SFTP service on/off by writing or not the
    `Subsystem sftp internal-sftp` (INTERNAL_SFTP_STR) declaration in SSHD_CONFIG.
    :param switch:
    :return:
    """
    fo, npath = mkstemp()
    written = False
    distro_id = distro.id()
    with open(SSHD_CONFIG[distro_id].sftp) as sfo, open(npath, "w") as tfo:
        for line in sfo.readlines():
            if re.match(INTERNAL_SFTP_STR, line) is not None:
                if switch and not written:
                    tfo.write("{}\n".format(INTERNAL_SFTP_STR))
                    written = True
            elif re.match(SSHD_HEADER, line) is not None:
                tfo.write(line)
                if switch and not written:
                    tfo.write("{}\n".format(INTERNAL_SFTP_STR))
                    written = True
            else:
                tfo.write(line)
    move(npath, SSHD_CONFIG[distro_id].sftp)
    try:
        run_command([SYSTEMCTL, "reload", "sshd"], log=True)
    except:
        return run_command([SYSTEMCTL, "restart", "sshd"], log=True)


def sftp_mount_map(mnt_prefix):
    mnt_map = {}
    with open("/proc/mounts") as pfo:
        for line in pfo.readlines():
            if re.search(" " + mnt_prefix, line) is not None:
                fields = line.split()
                sname = fields[1].split("/")[-1]
                editable = fields[3][:2]
                mnt_map[sname] = editable
    return mnt_map


def sftp_mount(share, mnt_prefix, sftp_mnt_prefix, mnt_map, editable="rw"):
    #  don't mount if already mounted
    sftp_mnt_pt = "{}{}/{}".format(sftp_mnt_prefix, share.owner, share.name)
    share_mnt_pt = "{}{}".format(mnt_prefix, share.name)
    if share.name in mnt_map:
        cur_editable = mnt_map[share.name]
        if cur_editable != editable:
            return run_command(
                [
                    MOUNT,
                    "-o",
                    "remount,{},bind".format(editable),
                    share_mnt_pt,
                    sftp_mnt_pt,
                ]
            )
    else:
        run_command([MKDIR, "-p", sftp_mnt_pt])
        run_command([MOUNT, "--bind", share_mnt_pt, sftp_mnt_pt])
        if editable == "ro":
            run_command(
                [
                    MOUNT,
                    "-o",
                    "remount,{},bind".format(editable),
                    share_mnt_pt,
                    sftp_mnt_pt,
                ]
            )


def rsync_for_sftp(chroot_loc):
    user = chroot_loc.split("/")[-1]
    run_command([MKDIR, "-p", "{}/bin".format(chroot_loc)], log=True)
    run_command([MKDIR, "-p", "{}/usr/bin".format(chroot_loc)], log=True)
    run_command([MKDIR, "-p", "{}/lib64".format(chroot_loc)], log=True)
    run_command([MKDIR, "-p", "{}/usr/lib64".format(chroot_loc)], log=True)

    copy("/bin/bash", "{}/bin".format(chroot_loc))
    copy("/usr/bin/rsync", "{}/usr/bin".format(chroot_loc))

    ld_linux_so = "/lib64/ld-linux-x86-64.so.2"
    if platform.machine() == "aarch64":
        ld_linux_so = "/lib64/ld-linux-aarch64.so.1"

    libs_d = {
        "rockstor": [
            ld_linux_so,
            "/lib64/libacl.so.1",
            "/lib64/libattr.so.1",
            "/lib64/libc.so.6",
            "/lib64/libdl.so.2",
            "/lib64/libpopt.so.0",
            "/lib64/libtinfo.so.5",
        ],
        # Account for distro 1.7.0 onwards reporting "opensuse" for id in opensuse-leap.
        "opensuse": [
            "/lib64/libacl.so.1",
            "/lib64/libz.so.1",
            "/usr/lib64/libpopt.so.0",
            "/usr/lib64/libslp.so.1",
            "/lib64/libc.so.6",
            "/lib64/libattr.so.1",
            "/usr/lib64/libcrypto.so.1.1",
            "/lib64/libpthread.so.0",
            ld_linux_so,
            "/lib64/libdl.so.2",
            "/lib64/libreadline.so.7",
            "/lib64/libtinfo.so.6",
        ],
        "opensuse-leap": [
            "/lib64/libacl.so.1",
            "/lib64/libz.so.1",
            "/usr/lib64/libpopt.so.0",
            "/usr/lib64/libslp.so.1",
            "/lib64/libc.so.6",
            "/lib64/libattr.so.1",
            "/usr/lib64/libcrypto.so.1.1",
            "/lib64/libpthread.so.0",
            ld_linux_so,
            "/lib64/libdl.so.2",
            "/lib64/libreadline.so.7",
            "/lib64/libtinfo.so.6",
        ],
        "opensuse-tumbleweed": [
            "/lib64/libc.so.6",
            "/usr/lib64/libacl.so.1",
            "/lib64/libz.so.1",
            "/usr/lib64/libpopt.so.0",
            "/usr/lib64/libslp.so.1",
            ld_linux_so,
            "/usr/lib64/libcrypto.so.1.1",
            "/lib64/libpthread.so.0",
            "/lib64/libdl.so.2",
            "/lib64/libreadline.so.8",
            "/lib64/libtinfo.so.6",
        ],
    }

    for l in libs_d[settings.OS_DISTRO_ID]:
        copy(l, "{}{}".format(chroot_loc, l))
    run_command([USERMOD, "-s", "/bin/bash", user], log=True)


def is_pub_key(key):
    fo, npath = mkstemp()
    with open(npath, "w") as tfo:
        tfo.write(key)
    try:
        run_command(["ssh-keygen", "-l", "-f", npath])
    except:
        return False
    finally:
        os.remove(npath)

    return True


def is_sftp_running(return_boolean=True):
    """
    Wrapper around system.osi.run_command() for parent sshd service status,
    followed by a check of is_sftp_subsystem_internal()
    to return a boolean for the SFTP service status
    which is a subsystem of the sshd systemd service.
    :return: status info of sftp sshd subsystem
    :rtype boolean or (out, err, rc
    """
    # Avoid potentially circular dependency on system.service by direct run_command use.
    out, err, rc = run_command(
        [SYSTEMCTL, "--lines=0", "status", "sshd"], throw=False, log=True
    )
    sftp_subsytem_found = False
    if rc == 0:
        sftp_subsytem_found = is_sftp_subsystem_internal()
        if not sftp_subsytem_found:
            rc = 1  # arbitrary rc value to indicate subsystem missing.
    if return_boolean:
        return sftp_subsytem_found
    else:
        return out, err, rc


def is_sftp_subsystem_internal(sshd_config=None):
    """
    Searches passed config file, or distro specific sftp file, for INTERNAL_SFTP_STR.
    :return: True if found
    :rtype Boolean:
    """
    # Default to the distro specific sshd sftp file
    if sshd_config is None:
        sshd_config = SSHD_CONFIG[distro.id()].sftp
    if not os.path.isfile(sshd_config):
        # a non existent file cannot contain our INTERNAL_SFTP_STR
        return False
    with open(sshd_config) as sfo:
        for line in sfo.readlines():
            if re.match(INTERNAL_SFTP_STR, line) is not None:
                return True
    return False


def remove_sftp_server_subsystem(sshd_config=None):
    """
    Basic search and remark out (in given file, or distro specific sshd default file),
    of 'Subsystem *sftp-server' line. Returning sshd to openssh defaults of no enabled
    Subsystem: enabling our consequent use of the sftp-internal subsystem.
    sftp-internal needs no additional configuration files when using chroot.
    :param sshd_config: Full path of sshd_config file.
    :return: True on replacement, False otherwise.
    :rtype boolean:
    """
    # Comment out OS default sftp subsystem (if sftp-server).
    # Default to the distro specific sshd OS default config.
    if sshd_config is None:
        sshd_config = SSHD_CONFIG[distro.id()].sshd_os
    found_and_replaced = False
    if os.path.isfile(sshd_config):
        fh, npath = mkstemp()
        with open(npath, "w+") as temp_file:
            # Original opened in 'r' (default) in text mode.
            with open(sshd_config) as original_file:
                for line in original_file.readlines():
                    if line.startswith("Subsystem") and line.endswith("sftp-server\n"):
                        temp_file.write("#{}\n".format(line))
                        found_and_replaced = True
                    else:
                        temp_file.write(line)
        if found_and_replaced:
            shutil.move(npath, sshd_config)
            logger.info("SSHD ({}) sftp-server disabled".format(sshd_config))
        else:
            logger.info("SSHD ({}) sftp-server already disabled".format(sshd_config))
            os.remove(npath)
    else:
        logger.info("SSHD file ({}) does not exist".format(sshd_config))
    return found_and_replaced
