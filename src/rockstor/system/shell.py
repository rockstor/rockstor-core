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

from osi import run_command
import shutil
from tempfile import mkstemp
from django.conf import settings

# Config file for /repositories/shells/.../shells.repo shellinabox package.
# This package references the following config file in it's service file.
SHELL_CONFIG = "/etc/sysconfig/shellinabox"
PREFIX = "SHELLINABOXD_"
# The to-be-legacy CentOS shellinabox package config
if settings.OS_DISTRO_ID == "rockstor":
    SHELL_CONFIG = "/etc/sysconfig/shellinaboxd"
    PREFIX = ""
SYSTEMCTL = "/usr/bin/systemctl"


def update_shell_config(shelltype="LOGIN", css="white-on-black"):
    fh, npath = mkstemp()
    with open(npath, "w") as tfo:
        # Write shellinaboxd default config
        tfo.write("# Shell In A Box configured by Rockstor\n\n")
        tfo.write("{}USER={}\n".format(PREFIX, settings.SHELLINABOX.get("user")))
        tfo.write("{}GROUP={}\n".format(PREFIX, settings.SHELLINABOX.get("group")))
        tfo.write("{}CERTDIR={}\n".format(PREFIX, settings.SHELLINABOX.get("certs")))
        tfo.write("{}PORT={}\n".format(PREFIX, settings.SHELLINABOX.get("port")))
        # Add config customization for css and shelltype
        # IMPORTANT
        # --localhost-only to block shell direct access and because behind
        # nginx --disable-ssl because already on rockstor ssl --no-beep to
        # avoid sounds and possible crashes under FF - see man pages
        tfo.write('{}OPTS="--no-beep --localhost-only --disable-ssl '.format(PREFIX))
        # Switch between LOGIN connection and SSH connection LOGIN connection
        # only uid > 1000 allowed, su required to become root\n SSH connection
        # root login allowed too
        tfo.write("-s /:{} ".format(shelltype))
        # If white on black add --css option Default black on white --css
        # option not required / shellinaboxd fails
        if css == "white-on-black":
            tfo.write("--css {}.css".format(css))
        # And we finally close quote and carriage return the compound OPTS line:
        tfo.write('"\n')
    shutil.move(npath, SHELL_CONFIG)


def restart_shell(sysd_name):
    # simply restart shellinaboxd service No return code checks because rc!=0
    # documented also for nicely running state
    return run_command([SYSTEMCTL, "restart", sysd_name])
