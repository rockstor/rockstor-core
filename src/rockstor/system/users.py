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

from exceptions import CommandException
from osi import run_command
import subprocess
import fcntl
import time
import re
import os
import pwd
import grp
from shutil import move
from tempfile import mkstemp
import chardet
import random
import string
import crypt

import logging

logger = logging.getLogger(__name__)

USERADD = "/usr/sbin/useradd"
GROUPADD = "/usr/sbin/groupadd"
USERDEL = "/usr/sbin/userdel"
GROUPDEL = "/usr/sbin/groupdel"
USERMOD = "/usr/sbin/usermod"
SMBPASSWD = "/usr/bin/smbpasswd"
CHOWN = "/usr/bin/chown"


# this is a hack for AD to get as many users as possible within 90 seconds.  If
# there are several thousands of domain users and AD isn't that fast, winbind
# takes a long time to enumerate the users for getent. Subsequent queries
# finish faster because of caching. But this prevents timing out.
def get_users(max_wait=90):
    t0 = time.time()
    users = {}
    p = subprocess.Popen(
        ["/usr/bin/getent", "passwd"],
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    fcntl.fcntl(p.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
    alive = True
    user_data = ""
    while alive:
        try:
            if p.poll() is not None:
                alive = False
            user_data += p.stdout.read()
        except IOError:
            if time.time() - t0 < max_wait:
                continue
        except Exception as e:
            logger.exception(e)
            p.terminate()
        uf = user_data.split("\n")
        # If the feed ends in \n, the last element will be '', if not, it will
        # be a partial line to be processed next time around.
        user_data = uf[-1]
        for u in uf[:-1]:
            ufields = u.split(":")
            if len(ufields) > 3:
                charset = chardet.detect(ufields[0])
                uname = ufields[0].decode(charset["encoding"])
                users[uname] = (int(ufields[2]), int(ufields[3]), str(ufields[6]))
            if time.time() - t0 > max_wait:
                p.terminate()
                break
    return users


def get_groups(*gids):
    groups = {}
    if len(gids) > 0:
        for g in gids:
            entry = grp.getgrgid(g)
            charset = chardet.detect(entry.gr_name)
            gr_name = entry.gr_name.decode(charset["encoding"])
            groups[gr_name] = entry.gr_gid
    else:
        for g in grp.getgrall():
            charset = chardet.detect(g.gr_name)
            gr_name = g.gr_name.decode(charset["encoding"])
            groups[gr_name] = g.gr_gid
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
    salt_header = "$6$"  # SHA-512
    rnd = random.SystemRandom()
    salt = "".join(
        [rnd.choice(string.ascii_letters + string.digits + "./") for _ in range(16)]
    )
    crypted_passwd = crypt.crypt(passwd.encode("utf8"), salt_header + salt)
    cmd = [USERMOD, "-p", crypted_passwd, username]
    p = subprocess.Popen(
        cmd,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
    )
    out, err = p.communicate(input=None)
    rc = p.returncode
    if rc != 0:
        raise CommandException(cmd, out, err, rc)
    return out, err, rc


def smbpasswd(username, passwd):
    cmd = [SMBPASSWD, "-s", "-a", username]
    p = subprocess.Popen(
        cmd,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
    )
    pstr = "%s\n%s\n" % (passwd, passwd)
    out, err = p.communicate(input=pstr.encode("utf8"))
    rc = p.returncode
    if rc != 0:
        raise CommandException(cmd, out, err, rc)
    return (out, err, rc)


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
        return ([""], [""], 0)

    cmd = [USERADD, "-s", shell, "-m", username]
    if uid is not None:
        cmd.insert(-1, "-u")
        cmd.insert(-1, str(uid))
    if gid is not None:
        cmd.insert(-1, "-g")
        cmd.insert(-1, str(gid))
    return run_command(cmd)


def groupadd(groupname, gid=None):
    cmd = [GROUPADD, groupname]
    if gid is not None:
        cmd.insert(-1, "-g")
        cmd.insert(-1, gid)
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
    os.chmod(SSH_DIR, 700)
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
    os.chmod(AUTH_KEYS, 600)
    run_command([CHOWN, "%s:%s" % (username, groupname), AUTH_KEYS])
