"""
Copyright (joint work) 2024 The Rockstor Project <https://rockstor.com>

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
import shutil
import stat
from shutil import move, copy
from tempfile import mkstemp
from pathlib import Path

import distro
from django.conf import settings

from fs.btrfs import umount_root
from system.osi import run_command, get_libs, is_mounted
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
    # Distro 1.7.0 onwards reports "opensuse" for id in Leap, including Leap 16.0.
    # Previous versions reported "opensuse-leap".
    "opensuse": sshd_files(
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


class SshdConfig:
    """
    Accessor class for SSHD_CONFIG's sshd_files type values dependent on distro.
    """

    def __init__(self):
        if distro.id() == "opensuse" and distro.version().startswith("15"):
            self.files: sshd_files = SSHD_CONFIG["opensuse"]
        else:
            self.files: sshd_files = SSHD_CONFIG["opensuse-tumbleweed"]


PROGS_IN_CHROOT = ["/usr/bin/bash", "/usr/bin/rsync", "/usr/bin/ls"]


def sshd_config_opener(path, flags):
    return os.open(path, flags, mode=stat.S_IRUSR | stat.S_IWUSR)


def init_sftp_config(sshd_config=None):
    """
    Establish our default sftp configuration within the distro specific file
    or a file passed by full path.
    :param sshd_config:
    :return: True if sshd configuration was modified, False otherwise.
    :rtype boolean:
    """
    if sshd_config is None:
        sshd_config = SshdConfig().files.sftp
    sshd_restart = False
    found = False
    if not os.path.isfile(sshd_config):
        logger.info(f"SSHD - Creating new configuration file ({sshd_config}).")
    else:
        with open(sshd_config, encoding="utf-8") as sfo:
            for line in sfo.readlines():
                if line.startswith(SSHD_HEADER):
                    found = True
                    logger.info(f"SSHD ({sshd_config}) already initialised")
                    break
    if not found:
        # Set initial AllowUsers and Subsystem sftp-internal configuration.
        # N.B. opening mode append with create-file if it doesn't exist.
        with open(
            sshd_config, mode="a+", encoding="utf-8", opener=sshd_config_opener
        ) as sfo:
            sshd_restart = True
            sfo.write(f"{SSHD_HEADER}\n")
            sfo.write(f"{INTERNAL_SFTP_STR}\n")
            # TODO Split out AllowUsers into SSHD_CONFIG[distro.id()].AllowUsers
            if os.path.isfile(f"{settings.CONFROOT}/PermitRootLogin"):
                sfo.write("AllowUsers root\n")
        logger.info(f"SSHD ({sshd_config}) initialised")
    return sshd_restart


def update_sftp_user_share_config(input_map):
    """
    Receives sftp-related customization settings and writes them to SSHD_CONFIG files.
    :param input_map: dictionary of chroot directory values keyed by username.
    :return:
    """
    fo, npath = mkstemp()
    sshd_conf = SshdConfig()
    # TODO: Split out AllowUsers into SSHD_CONFIG[distro.id()].AllowUsers
    userstr = "AllowUsers"
    if os.path.isfile(f"{settings.CONFROOT}/PermitRootLogin"):
        userstr += " root {}".format(" ".join(input_map.keys()))
    else:
        userstr += " {}".format(" ".join(input_map.keys()))
    with open(sshd_conf.files.sftp) as sfo, open(npath, "w") as tfo:
        for line in sfo.readlines():
            if re.match(SSHD_HEADER, line) is None:
                tfo.write(line)
            else:
                break
        tfo.write(f"{SSHD_HEADER}\n")
        # Detect sftp service status and ensure we maintain it
        if is_sftp_running():
            tfo.write(f"{INTERNAL_SFTP_STR}\n")
        tfo.write(f"{userstr}\n")
        # Set options for each user according to openSUSE's defaults:
        # https://en.opensuse.org/SDB:SFTP_server_with_Chroot#Match_rule_block
        # TODO: implement webUI element to re-enable rsync over ssh by omitting
        #   the `ForceCommand internal-sftp` line below.
        for user in input_map:
            tfo.write(f"Match User {user}\n")
            tfo.write("\tForceCommand internal-sftp\n")
            tfo.write(f"\tChrootDirectory {input_map[user]}\n")
            tfo.write("\tX11Forwarding no\n")
            tfo.write("\tAllowTcpForwarding no\n")

    move(npath, sshd_conf.files.sftp)
    try:
        run_command([SYSTEMCTL, "reload", "sshd"], log=True)
    except:
        return run_command([SYSTEMCTL, "restart", "sshd"], log=True)


def toggle_sftp_service(switch=True):
    """
    Toggles the SFTP service on/off by writing or removing the
    `Subsystem sftp internal-sftp` (INTERNAL_SFTP_STR) declaration in SSHD_CONFIG.
    :param switch:
    :return:
    """
    fo, npath = mkstemp()
    sshd_conf = SshdConfig()
    written = False
    with open(sshd_conf.files.sftp) as sfo, open(npath, "w") as tfo:
        for line in sfo.readlines():
            if re.match(INTERNAL_SFTP_STR, line) is not None:
                if switch and not written:
                    tfo.write(f"{INTERNAL_SFTP_STR}\n")
                    written = True
            elif re.match(SSHD_HEADER, line) is not None:
                tfo.write(line)
                if switch and not written:
                    tfo.write(f"{INTERNAL_SFTP_STR}\n")
                    written = True
            else:
                tfo.write(line)
    move(npath, sshd_conf.files.sftp)
    try:
        run_command([SYSTEMCTL, "reload", "sshd"], log=True)
    except:
        return run_command([SYSTEMCTL, "restart", "sshd"], log=True)


def sftp_mount_map(mnt_prefix):
    """
    Returns Share.name indexed dictionary of /mnt_prefix/*share.name active mounts.
    I.e. with mnt_prefix="/mnt3/" the bind mount location, within a users chroot,
    that we expose SFTP Exported Shares.
    :param mnt_prefix: normally settings.SFTP_MNT_ROOT
    :return: E.g.: {'sftp-share1a': 'rw', 'sftp-share1': 'rw', 'sftp-share2': 'ro'}
    or {} if no intended SFTP chroot mnt_points found.
    """
    mnt_map = {}
    with open("/proc/mounts") as pfo:
        for line in pfo.readlines():
            if re.search(" " + mnt_prefix, line) is not None:
                fields = line.split()
                sname = fields[1].split("/")[-1]
                editable = fields[3][:2]
                mnt_map[sname] = editable
    logger.info(f" ***DEV: sftp_mount_map() returning {mnt_map}")
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


def remove_sftp_bindmounts(
    share_name: str, snap_name_list: list[str], chroot_path: str
):
    """
    Unmount SFTP bind mounts associated with each contained share.owner's chroot_path.
    :param share_name: A SFTP Share.name to unmount from within the given chroot_path.
    :param snap_name_list: List of visible snapshot.names to unmount from within the
    chroot_path mounted share.
    :param chroot_path:
    """
    # We do a lot of repeat calls to is_mounted here.
    # Better to grab a dictionary of all mounts and reference it locally.
    sftp_export_path = f"{chroot_path}{share_name}"
    if is_mounted(sftp_export_path):  # SFTP in-chroot bind-mount.
        for visible_snap_name in snap_name_list:
            # E.g. "mnt3/share.owner/share.name/.visible_share_snapshot_name
            if is_mounted(f"{sftp_export_path}/.{visible_snap_name}"):
                # TODO: We need a lazy unmount here and a possible re-try.
                #  See nfs4_mount_teardown() in system/nfs_util.py
                umount_root(f"{sftp_export_path}/.{visible_snap_name}")
        umount_root(sftp_export_path)
        if os.path.isdir(sftp_export_path):
            shutil.rmtree(sftp_export_path)


def rsync_for_sftp(chroot_loc: str | Path):
    """
    Populate passed chroot_loc path with libraries sufficient for PROGS_IN_CHROOT.
    Dependencies retrieved via ldd.
    """
    chroot_path = Path(chroot_loc)
    user = chroot_path.name

    # Create all required subdirectories
    # TODO: See whether explicit directory creations (aside from /usr/bin) are not necessary anymore
    # with dynamic parent directory creation below
    bin_dir = chroot_path / "usr" / "bin"
    for sub_dir in [
        bin_dir,
        chroot_path / "lib",
        chroot_path / "lib64",
        chroot_path / "usr" / "lib64",
    ]:
        run_command([MKDIR, "-p", str(sub_dir)], log=True)

    # filter list for path components not needed in chroot environment
    FILTER_DIRS = {"zlib-ng-compat"}

    # TODO: determine whether get_libs() can also be refactored to accept and return path objects
    lib_list: list[str] = []

    # Copy chroot binaries and resolve lib dependencies
    for prog in PROGS_IN_CHROOT:
        prog_path = Path(prog)
        # Copy binary explicitly to target destination path
        copy(prog_path, bin_dir / prog_path.name)
        lib_list.extend(get_libs(prog))

    # Copy libs for PROGS_IN_CHROOT to chroot
    for lib in set(lib_list):
        path_obj = Path(lib)

        # Filter out unwanted directories
        filtered_parts = [part for part in path_obj.parts if part not in FILTER_DIRS]
        clean_lib_path = Path(*filtered_parts)

        # Assemble target path
        chroot_target = chroot_path / clean_lib_path.relative_to(path_obj.anchor)

        # Ensure parent directory exists before copying, then copy library
        chroot_target.parent.mkdir(parents=True, exist_ok=True)
        copy(path_obj, chroot_target)

    # Explicitly make bash the user shell
    run_command([USERMOD, "-s", "/usr/bin/bash", user], log=True)


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
        sshd_config = SshdConfig().files.sftp
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
        sshd_config = SshdConfig().files.sshd_os
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
            logger.info(f"SSHD ({sshd_config}) sftp-server disabled")
        else:
            logger.info(f"SSHD ({sshd_config}) sftp-server already disabled")
            os.remove(npath)
    else:
        logger.info(f"SSHD file ({sshd_config}) does not exist")
    return found_and_replaced
