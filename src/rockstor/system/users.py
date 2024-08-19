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
import crypt
import logging
import os
import pwd
import re
import stat
from shutil import move
from subprocess import run, Popen, PIPE
from tempfile import mkstemp
from typing import Union, Optional, Dict, Any

import dbus
import grp

from system.exceptions import CommandException
from system.osi import run_command
from system.services import is_systemd_service_active

logger = logging.getLogger(__name__)

USERADD = "/usr/sbin/useradd"
GROUPADD = "/usr/sbin/groupadd"
USERDEL = "/usr/sbin/userdel"
GROUPDEL = "/usr/sbin/groupdel"
USERMOD = "/usr/sbin/usermod"
SMBPASSWD = "/usr/bin/smbpasswd"
CHOWN = "/usr/bin/chown"

IFP_CONSTANTS = {
    "ifp_users": {
        "obj_path": "/org/freedesktop/sssd/infopipe/Users",
        "main_iface": "org.freedesktop.sssd.infopipe.Users",
        "sub_iface": "org.freedesktop.sssd.infopipe.Users.User",
    },
    "ifp_groups": {
        "obj_path": "/org/freedesktop/sssd/infopipe/Groups",
        "main_iface": "org.freedesktop.sssd.infopipe.Groups",
        "sub_iface": "org.freedesktop.sssd.infopipe.Groups.Group",
    },
}


# this is a hack for AD to get as many users as possible within 60 seconds.  If
# there are several thousands of domain users and AD isn't that fast, winbind
# takes a long time to enumerate the users for getent. Subsequent queries
# finish faster because of caching. But this prevents timing out.
def get_users(max_wait=60):
    users = {}
    # TODO: In Python 3.7 we have a capture_output option.
    result = run(
        ["/usr/bin/getent", "passwd"],
        shell=False,
        stdout=PIPE,
        stderr=PIPE,
        encoding="utf-8",
        # stdout and stderr as string
        universal_newlines=True,  # 3.7 adds text parameter universal_newlines alias
        timeout=max_wait,
    )
    out = result.stdout
    # TODO: Report & handle exception reported via CompletedProcess (result)
    out_list = out.split("\n")
    # out_list looks like;
    # ['root:x:0:0:root:/root:/bin/bash', ...
    # 'radmin:x:1000:100::/home/radmin:/bin/bash', '']
    for line in out_list[:-1]:  # skip empty last line.
        fields = line.split(":")
        if len(fields) > 3:
            uname = fields[0]
            users[uname] = (int(fields[2]), int(fields[3]), str(fields[6]))
    return users


def get_groups(*gids):
    groups = {}
    if len(gids) > 0:
        for g in gids:
            try:
                entry = grp.getgrgid(g)
                # Assume utf-8 encoded gr_name str
                gr_name = entry.gr_name
                groups[gr_name] = entry.gr_gid
            except KeyError:
                # The block above can sometimes fail for domain users (AD/LDAP)
                # as grp may not see them freshly after joining the domain.
                # Try to fetch requested info from InfoPipe as a fallback
                ifp_res = ifp_get_properties_from_name_or_id(
                    "ifp_groups", int(g), "name", "gidNumber"
                )
                groups[ifp_res["name"]] = int(ifp_res["gidNumber"])
                logger.debug(
                    "InfoPipe was used to fetch info for gid {}"
                    "name: {}, gid: {}".format(
                        g, ifp_res["name"], int(ifp_res["gidNumber"])
                    )
                )
    else:
        for g in grp.getgrall():
            # Assume utf-8 encoded gr_name str
            gr_name = g.gr_name
            groups[gr_name] = g.gr_gid

        # If sssd.service is running:
        # Fetch remote groups from InfoPipe and add missing ones to dict
        if not is_systemd_service_active("sssd"):
            return groups
        try:
            ifp_groups = ifp_get_groups()
            for ifp_gp, ifp_gid in ifp_groups.items():
                if ifp_gp not in groups:
                    groups[ifp_gp] = ifp_gid
        except dbus.DBusException as e:
            logger.debug(f"Exception while getting groups from InfoPipe: {e}")
            pass
    return groups


def userdel(uname):
    try:
        pwd.getpwnam(uname)
    except KeyError:
        # user doesn't exist
        return
    # Ensure user get deleted from samba pass db
    run_command([SMBPASSWD, "-x", uname])

    return run_command([USERDEL, "-r", uname])


def groupdel(groupname):
    try:
        return run_command([GROUPDEL, groupname])
    except CommandException as e:
        if e.rc != 6:
            raise e


def get_epasswd(username):
    with open("/etc/shadow") as sfo:
        for l in sfo.readlines():
            fields = l.split(":")
            if re.match(fields[0], username) is not None:
                return fields[1]
    return None


def usermod(username, passwd):
    # TODO: 'salt = crypt.mksalt()' # Python 3.3 onwards provides system best.
    # Salt starting "$6$" & of 19 chars signifies SHA-512 current system best.
    # Salt must contain only [./a-zA-Z0-9] chars (bar first 3 if len > 2)
    # salt_header = "$6$"  # SHA-512
    # rnd = random.SystemRandom()
    # salt = "".join(
    #     [rnd.choice(string.ascii_letters + string.digits + "./") for _ in range(16)]
    # )
    # crypted_passwd = crypt.crypt(passwd.encode("utf8"), salt_header + salt)
    salt = crypt.mksalt()
    crypted_passwd = crypt.crypt(passwd, salt)
    cmd: list[str] = [USERMOD, "-p", crypted_passwd, username]
    out, err, rc = run_command(cmd, log=True)
    # p = subprocess.Popen(
    #     cmd,
    #     shell=False,
    #     stdout=subprocess.PIPE,
    #     stderr=subprocess.PIPE,
    #     stdin=subprocess.PIPE,
    # )
    # out, err = p.communicate(input=None)
    # rc = p.returncode
    # if rc != 0:
    #     raise CommandException(cmd, out, err, rc)
    return out, err, rc


def smbpasswd(username, passwd):
    cmd = [SMBPASSWD, "-s", "-a", username]
    p = Popen(
        cmd,
        shell=False,
        stdout=PIPE,
        stderr=PIPE,
        stdin=PIPE,
    )
    pstr = "%s\n%s\n" % (passwd, passwd)
    out, err = p.communicate(input=pstr.encode("utf8"))
    rc = p.returncode
    if rc != 0:
        raise CommandException(cmd, out, err, rc)
    return out, err, rc


def update_shell(username, shell):
    return run_command([USERMOD, "-s", shell, username])


def useradd(username, shell, uid=None, gid=None):
    pw_entry = None
    try:
        # Use unix password db to assess prior user status by name
        pw_entry = pwd.getpwnam(username)
    except:
        pass
    if pw_entry is not None:
        # If we have a prior user by name assess uid gid mismatches.
        if uid is not None and uid != pw_entry.pw_uid:
            raise Exception(
                "User({0}) already exists, but her uid({1}) is "
                "different from the input({2}).".format(username, pw_entry.pw_uid, uid)
            )
        if gid is not None and gid != pw_entry.pw_gid:
            raise Exception(
                "User({0}) already exists, but her gid({1}) is "
                "different from the input({2}).".format(username, pw_entry.pw_gid, gid)
            )
        if shell != pw_entry.pw_shell:
            raise Exception(
                "User({0}) already exists, but her shell({1}) is "
                "different from the input({2}).".format(username, pw_entry.shell, shell)
            )
        return [""], [""], 0

    cmd: list[str] = [USERADD, "-s", shell, "-m", username]
    if uid is not None:
        cmd.insert(-1, "-u")
        cmd.insert(-1, str(uid))
    if gid is not None:
        cmd.insert(-1, "-g")
        cmd.insert(-1, str(gid))
    return run_command(cmd)


def groupadd(groupname: str, gid: int | None = None):
    cmd: list[str] = [GROUPADD, groupname]
    if gid is not None:
        cmd.insert(-1, "-g")
        cmd.insert(-1, str(gid))
    return run_command(cmd)


def add_ssh_key(username, key, old_key=None):
    groupname = grp.getgrgid(pwd.getpwnam(username).pw_gid).gr_name
    SSH_DIR = "/home/%s/.ssh" % username
    AUTH_KEYS = "%s/authorized_keys" % SSH_DIR
    openmode = "r"
    if not os.path.isfile(AUTH_KEYS):
        openmode = "a+"
    if not os.path.isdir(SSH_DIR):
        os.mkdir(SSH_DIR)
    run_command([CHOWN, "-R", "%s:%s" % (username, groupname), SSH_DIR])
    # Set directory to rwx --- --- (700) via stat constants.
    os.chmod(SSH_DIR, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    fo, npath = mkstemp()
    exists = False
    with open(AUTH_KEYS, openmode) as afo, open(npath, "w") as tfo:
        for line in afo.readlines():
            if line.strip("\n") == key:
                exists = True
            if line.strip("\n") == old_key:
                continue
            tfo.write(line)
        if not exists and key is not None:
            tfo.write("%s\n" % key)
    if exists:
        return os.remove(npath)
    move(npath, AUTH_KEYS)
    # Set file to rw- --- --- (600) via stat constants.
    os.chmod(AUTH_KEYS, stat.S_IRUSR | stat.S_IWUSR)
    run_command([CHOWN, "%s:%s" % (username, groupname), AUTH_KEYS])


def ifp_get_properties_from_name_or_id(
    iface_type: str, target: Union[str, int], *obj_properties: str
) -> Optional[Dict[str, Any]]:
    """Get user of group properties from InfoPipe

    Uses InfoPipe (SSSD D-Bus responder) to get desired properties
    from either a username/uid, or from a group name/gid.
    :param str iface_type: ifp_users or ifp_groups
    :param target: username/uid or groupname/gid
    :type target: str or int
    :param str obj_properties: properties to fetch
    :return: Dict of property name:value
    :raises Exception: if target is not a str or int
    """
    # InfoPipe depends on the sssd service running:
    if not is_systemd_service_active("sssd"):
        return None
    try:
        bus = dbus.SystemBus()
        ifp_bus_name = "org.freedesktop.sssd.infopipe"
        ifp_obj = bus.get_object(ifp_bus_name, IFP_CONSTANTS[iface_type]["obj_path"])
        ifp_iface = dbus.Interface(ifp_obj, IFP_CONSTANTS[iface_type]["main_iface"])

        if isinstance(target, str):
            my_obj = bus.get_object(ifp_bus_name, ifp_iface.FindByName(target))
        elif isinstance(target, int):
            my_obj = bus.get_object(ifp_bus_name, ifp_iface.FindByID(target))
        else:
            raise Exception(
                "Incompatible type for target {}: {}.".format(target, type(target))
            )

        my_iface_properties = dbus.Interface(my_obj, "org.freedesktop.DBus.Properties")

        ifp_res = {}
        for obj_property in obj_properties:
            ifp_res[obj_property] = my_iface_properties.Get(
                IFP_CONSTANTS[iface_type]["sub_iface"], obj_property
            )
        return ifp_res
    except dbus.DBusException as e:
        logger.debug(
            f"Exception while getting {obj_properties} for {target} on {iface_type}: {e}"
        )
        return None


def ifp_get_groups():
    """
    List all groups as seen by InfoPipe (SSSD D-Bus responder).
    :return: Dict - groupname as key, group gid as value
    """
    bus = dbus.SystemBus()
    groups_obj = bus.get_object(
        "org.freedesktop.sssd.infopipe", "/org/freedesktop/sssd/infopipe/Groups"
    )
    groups_iface = dbus.Interface(groups_obj, "org.freedesktop.sssd.infopipe.Groups")

    allgroups = groups_iface.ListByName("*", 0)
    ifp_groups = {}
    for group in allgroups:
        my_obj = bus.get_object("org.freedesktop.sssd.infopipe", group)
        my_obj_properties = dbus.Interface(my_obj, "org.freedesktop.DBus.Properties")
        gpname = my_obj_properties.Get(
            "org.freedesktop.sssd.infopipe.Groups.Group", "name"
        )
        gpid = my_obj_properties.Get(
            "org.freedesktop.sssd.infopipe.Groups.Group", "gidNumber"
        )
        ifp_groups[str(gpname)] = int(gpid)
    return ifp_groups
