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

from osi import inplace_replace
from tempfile import mkstemp
from shutil import move
import logging

logger = logging.getLogger(__name__)

NETWORK_FILE = "/etc/sysconfig/network"
AUTH_FILE = "/etc/sysconfig/authconfig"
YP_FILE = "/etc/yp.conf"
NSSWITCH_FILE = "/etc/nsswitch.conf"


def configure_nis(nis_domain, server):

    fo, npath = mkstemp()
    nl = "NISDOMAIN=%s\n" % nis_domain
    inplace_replace(NETWORK_FILE, npath, ("NISDOMAIN",), (nl,))
    fo, apath = mkstemp()
    inplace_replace(AUTH_FILE, apath, ("USENIS",), ("USENIS=yes\n",))
    fo, ypath = mkstemp()
    nl = "domain %s server %s\n" % (nis_domain, server)
    inplace_replace(YP_FILE, ypath, ("domain",), (nl,))
    fo, nspath = mkstemp()
    regex = (
        "passwd:",
        "shadow:",
        "group:",
        "hosts:",
    )
    nl = (
        "passwd:    files nis\n",
        "shadow:    files nis\n",
        "group:     files nis\n",
        "hosts:     files dns nis\n",
    )
    inplace_replace(NSSWITCH_FILE, nspath, regex, nl)
    move(npath, NETWORK_FILE)
    move(apath, AUTH_FILE)
    move(ypath, YP_FILE)
    move(nspath, NSSWITCH_FILE)
