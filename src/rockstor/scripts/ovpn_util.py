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

DOCKER = "/usr/bin/docker"
CMD = "%s run --volumes-from ovpn-data --rm" % DOCKER
image = "kylemanna/openvpn"


def initpki():
    os.system(
        "/usr/bin/docker run --volumes-from ovpn-data --rm "
        "-it kylemanna/openvpn ovpn_initpki"
    )


def client_gen():
    client_name = raw_input("Enter a name for the client(no spaces): ")  # noqa F821
    os.system(
        "%s -it %s easyrsa build-client-full %s nopass" % (CMD, image, client_name)
    )


def client_retrieve():
    client_name = raw_input(
        "Enter the name of the client you like to retrieve: "
    )  # noqa F821 E501
    outfile = "/tmp/%s.ovpn" % client_name
    rc = os.system("%s %s ovpn_getclient %s > %s" % (CMD, image, client_name, outfile))
    if rc == 0:
        print(
            "client configuration is saved at %s. It can be used by your "
            "vpn client software to connect." % outfile
        )
