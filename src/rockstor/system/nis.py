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

from system.osi import inplace_replace
from tempfile import mkstemp
from shutil import move
import logging

logger = logging.getLogger(__name__)

NETWORK_FILE = "/etc/sysconfig/network/config"
# AUTH_FILE = "/etc/sysconfig/authconfig"
YP_FILE = "/etc/yp.conf"
NSSWITCH_FILE = "/etc/nsswitch.conf"


def configure_nis(nis_domain, server):
    """
    In NETWORK_FILE:
    Adds/edits NETCONFIG_NIS_STATIC_DOMAIN to equal nis_domain.
    Adds/edits NETCONFIG_NIS_STATIC_SERVERS to equal server.
    In YP_FILE:
    Adds/edits domain entry to equal "domain $nis_domain server $server"
    In NSSWITCH_FILE:
    Adds/edits passwd,shadow,group entries to equal "files nis"
    Adds/edits hosts entries to equal  "files mdns_minimal [NOTFOUND=return] dns nis"
    https://doc.opensuse.org/documentation/leap/security/html/book-security/cha-nis.html
    :param nis_domain: User input NIS domain e.g. "example.com", or "lan".
    :param server: User input NIS server e.g. "192.168.1.159"
    """

    fo, npath = mkstemp()
    # post yast nis client setup
    # In /etc/sysconfig/network/config
    # NETCONFIG_NIS_SETDOMAINNAME="yes" (default "netconfig sets the domainname")
    # Defines whether to set the default NIS domain. When enabled and no domain
    # is provided dynamically or in static settings, /etc/defaultdomain is used.
    # Typically, a Rockstor install will have an empty /etc/defaultdomain.
    # NETCONFIG_NIS_STATIC_DOMAIN="" (default)
    # NETCONFIG_NIS_STATIC_SERVERS="" (default)
    regex = ("NETCONFIG_NIS_STATIC_DOMAIN", "NETCONFIG_NIS_STATIC_SERVERS")
    nl = (
        'NETCONFIG_NIS_STATIC_DOMAIN="{}"\n'.format(nis_domain),
        'NETCONFIG_NIS_STATIC_SERVERS="{}"\n'.format(server),
    )
    inplace_replace(NETWORK_FILE, npath, regex, nl)
    # Legacy CentOS section:
    # fo, apath = mkstemp()
    # authconfig is RH Fedora tool, authselect is partial counterpart in Tumbleweed only.
    # inplace_replace(AUTH_FILE, apath, ("USENIS",), ("USENIS=yes\n",))
    fo, ypath = mkstemp()
    nl = "domain {} server {}\n".format(nis_domain, server)
    inplace_replace(YP_FILE, ypath, ("domain",), (nl,))
    fo, nspath = mkstemp()
    regex = ("passwd:", "shadow:", "group:", "hosts:")
    # We mimic yast2-nis-client plugin behaviour with the following multiple entries.
    nl = (
        "passwd:    files nis\n",
        "shadow:    files nis\n",
        "group:     files nis\n",
        # mdns_minimal [NOTFOUND=return] is added by nss-mdns: an avahi dependency
        "hosts:     files mdns_minimal [NOTFOUND=return] dns nis\n",
    )
    inplace_replace(NSSWITCH_FILE, nspath, regex, nl)
    move(npath, NETWORK_FILE)
    # move(apath, AUTH_FILE)
    move(ypath, YP_FILE)
    move(nspath, NSSWITCH_FILE)
