"""
Copyright (c) 2012-2021 RockStor, Inc. <http://rockstor.com>
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

import collections
import json
import logging

from system.osi import run_command
from system.services import service_status

Image = collections.namedtuple("Image", "repository tag image_id created virt_size")
Container = collections.namedtuple(
    "Container", "container_id image command created status ports name"
)

DOCKER = "/usr/bin/docker"
DNET = [
    DOCKER,
    "network",
]

logger = logging.getLogger(__name__)


def image_list():
    """
    Appears to be unused currently.
    :return:
    """
    images = []
    o, e, rc = run_command([DOCKER, "images"])
    for l in o[1:-1]:
        cur_image = Image(
            l[0:20].strip(),
            l[20:40].strip(),
            l[40:60].strip(),
            l[60:80].strip(),
            l[80:].strip(),
        )
        images.append(cur_image)
    return images


def container_list():
    """
    Appears to be unused currently.
    :return:
    """
    containers = []
    o, e, rc = run_command([DOCKER, "ps", "-a"])
    for l in o[1:-1]:
        cur_con = Container(
            l[0:20].strip(),
            l[20:40].strip(),
            l[40:60].strip(),
            l[60:80].strip(),
            l[80:100].strip(),
            l[100:120].strip(),
            l[120:].strip(),
        )
        containers.append(cur_con)
    return containers


def docker_status():
    o, e, rc = service_status("docker")
    if rc != 0:
        return False
    return True


def dnets(id=None, type=None):
    """
    List the docker names of all docker networks.
    :param id: string, used to test for network presence.
    :param type: string, either 'custom' or 'builtin'
    :return: list
    """
    cmd = list(DNET) + [
        "ls",
        "--format",
        "{{.Name}}",
    ]
    if id:
        cmd.extend(["--filter", "id={}".format(id)])
    if type is not None:
        if type == "custom":
            cmd.extend((["--filter", "type=custom"]))
        elif type == "builtin":
            cmd.extend((["--filter", "type=builtin"]))
        else:
            raise Exception("type must be custom or builtin")
    o, e, rc = run_command(cmd)
    return o[:-1]


def dnet_inspect(dname):
    """
    This function takes the name of a docker network as argument
    and returns a dict of its configuration.
    :param dname: docker network name
    :return: dict
    """
    cmd = list(DNET) + ["inspect", dname, "--format", "{{json .}}"]
    o, _, _ = run_command(cmd)
    return json.loads(o[0])


def probe_containers(container=None, network=None, all=False):
    """
    List docker containers.
    :param container: container name
    :param network:
    :param all:
    :return:
    """
    cmd = [
        DOCKER,
        "ps",
        "--format",
        "{{.Names}}",
    ]
    if docker_status():
        if all:
            cmd.extend(
                ["-a",]
            )
        if network:
            cmd.extend(
                ["--filter", "network={}".format(network),]
            )
        if container:
            cmd.extend(
                ["--filter", "name={}".format(container),]
            )
        o, e, rc = run_command(cmd)
        return o


def dnet_create(
    network,
    aux_address=None,
    dgateway=None,
    host_binding=None,
    icc=None,
    internal=None,
    ip_masquerade=None,
    ip_range=None,
    mtu=1500,
    subnet=None,
):
    """
    This method checks for an already existing docker network with the same name.
    If none is found, it will be created using the different parameters given.
    If no parameter is specified, the network will be created using docker's defaults.
    :param network:
    :param aux_address:
    :param dgateway:
    :param host_binding:
    :param icc:
    :param internal:
    :param ip_masquerade:
    :param ip_range:
    :param mtu:
    :param subnet:
    :return:
    """
    if not docker_status():
        raise Exception(
            "Cannot create rocknet while docker is not running. "
            "Turn the Rock-on service ON and try again"
        )
    o, e, rc = run_command(list(DNET) + ["list", "--format", "{{.Name}}",])
    if network not in o:
        logger.debug(
            "the network {} was NOT detected, so create it now.".format(network)
        )
        cmd = list(DNET) + [
            "create",
        ]
        if subnet is not None and len(subnet.strip()) > 0:
            cmd.extend(
                ["--subnet={}".format(subnet),]
            )
        if dgateway is not None and len(dgateway.strip()) > 0:
            cmd.extend(
                ["--gateway={}".format(dgateway),]
            )
        if aux_address is not None and len(aux_address.strip()) > 0:
            for i in aux_address.split(","):
                cmd.extend(
                    ['--aux-address="{}"'.format(i.strip()),]
                )
        if host_binding is not None and len(host_binding.strip()) > 0:
            cmd.extend(
                [
                    "--opt",
                    "com.docker.network.bridge.host_binding_ipv4={}".format(
                        host_binding
                    ),
                ]
            )
        if icc is True:
            cmd.extend(
                ["--opt", "com.docker.network.bridge.enable_icc=true",]
            )
        if internal is True:
            cmd.extend(
                ["--internal",]
            )
        if ip_masquerade is True:
            cmd.extend(
                ["--opt", "com.docker.network.bridge.enable_ip_masquerade=true",]
            )
        if ip_range is not None and len(ip_range.strip()) > 0:
            cmd.extend(
                ["--ip-range={}".format(ip_range),]
            )
        if mtu != 1500:
            cmd.extend(
                ["--opt", "com.docker.network.driver.mtu={}".format(mtu),]
            )
        cmd.extend(
            [network,]
        )
        run_command(cmd, log=True)
    else:
        logger.debug(
            "the network {} was detected, so do NOT create it.".format(network)
        )


def dnet_connect(container, network, all=False):
    """
    Simple wrapper around docker connect with prior check for the existence of the container
    and the lack of current connection to desired network.
    :param container:
    :param network:
    :param all:
    :return:
    """
    if (container in probe_containers(container=container, all=all)) and (
        container not in probe_containers(network=network, all=all)
    ):
        run_command(list(DNET) + ["connect", network, container,], log=True)


def dnet_disconnect(container, network):
    run_command(list(DNET) + ["disconnect", network, container,], log=True)


def dnet_remove(network=None):
    """
    This method uses the docker toolset to remove a docker network.
    As this would throw an error if the network does not exist, we need
    to first verify its presence.
    :param network: string of network name as seen by `docker network ls`
    :return:
    """
    # First, verify the network still exists
    if network in dnets():
        run_command(list(DNET) + ["rm", network,], log=True)
