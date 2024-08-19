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

import json
import logging
import os
import re

from system.docker import dnets, docker_status, dnet_inspect
from system.exceptions import CommandException
from system.osi import run_command, to_boolean

NMCLI = "/usr/bin/nmcli"
DEFAULT_MTU = 1500
SYSCTL = "/sbin/sysctl"
SYSCTL_CONFD_PATH = "/etc/sysctl.d/"
logger = logging.getLogger(__name__)


def val(s):
    fields = s.split(": ")
    if len(fields) < 2:
        return None
    v = fields[1].strip()
    if len(v) == 0 or v == "--":
        return None
    return v


def get_dev_list():
    """
    Returns a list of connection devices as seen by Network Manager
    :return: list
    """
    o, e, rc = run_command([NMCLI, "-t", "-f", "device", "device"])
    return o


def get_dev_config(dev_list):
    """
    Takes a list of connection devices and returns a dictionary with
    each device's config as seen by Network Manager
    :param dev_list: list returned by get_dev_list()
    :return: dictionary
    """
    dmap = {}
    for dev in dev_list:
        if len(dev.strip()) == 0:
            continue
        tmap = {
            "dtype": None,
            "mac": None,
            "mtu": None,
            "state": None,
        }
        try:
            o, e, r = run_command([NMCLI, "d", "show", dev])
        except CommandException as e:
            # especially veth devices can vanish abruptly sometimes.
            if e.rc == 10:
                logger.exception(e)
                logger.debug("device: {} vanished. Discarding it".format(dev))
                continue
            raise

        for l in o:
            if re.match("GENERAL.TYPE:", l) is not None:
                tmap["dtype"] = val(l)
            elif re.match("GENERAL.HWADDR:", l) is not None:
                tmap["mac"] = val(l)
            elif re.match("GENERAL.MTU:", l) is not None:
                tmap["mtu"] = val(l)
            elif re.match("GENERAL.STATE:", l) is not None:
                tmap["state"] = val(l)
            elif re.match("GENERAL.CONNECTION:", l) is not None:
                connection = val(l)
                if connection is not None:
                    tmap["connection"] = connection
        dmap[dev] = tmap
    return dmap


def get_con_list():
    """
    Returns a list of connections as seen by Network Manager.
    :return: list
    """
    o, e, rc = run_command(
        [
            NMCLI,
            "-t",
            "-f",
            "uuid",
            "c",
            "show",
        ]
    )
    return o


def get_con_config(con_list):
    """
    Takes a list of connections and returns a dictionary with
    each connection's config as seen by Network Manager
    :param con_list: list returned by get_con_list()
    :return: dictionary
    """
    cmap = {}

    def flatten(l):
        s = ",".join(l)
        if len(s) == 0:
            return None
        return s

    def parse_aux_addresses(dtmap):
        """
        Parses auxiliary addresses of a docker network and
        returns a flat list.
        :param dtmap:
        :return:
        """
        aux = dtmap["IPAM"]["Config"][0]["AuxiliaryAddresses"]
        aux_list = []
        for k, v in aux.items():
            aux_list.append("{}={}".format(k, v))
        return flatten(aux_list)

    for uuid in con_list:
        if len(uuid.strip()) == 0:
            continue
        tmap = {
            "name": None,
            "state": None,
            "ipv4_method": None,
            "ipv4_addresses": [],
            "ipv4_gw": None,
            "ipv4_dns": [],
            "ipv4_dns_search": None,
            "ipv6_method": None,
            "ipv6_addresses": None,
            "ipv6_gw": None,
            "ipv6_dns": None,
            "ipv6_dns_search": None,
        }
        try:
            o, e, rc = run_command(
                [
                    NMCLI,
                    "c",
                    "show",
                    uuid,
                ]
            )
        except CommandException as e:
            # in case the connection disappears
            if e.rc == 10:
                logger.exception(e)
                logger.debug("connection: {} vanished. Discarding it".format(uuid))
                continue
            raise e
        for l in o:
            if re.match("ipv4.method:", l) is not None:
                tmap["ipv4_method"] = val(l)
            elif re.match("connection.id:", l) is not None:
                tmap["name"] = val(l)
            elif re.match("GENERAL.STATE:", l) is not None:
                tmap["state"] = val(l)
            elif re.match("IP4.ADDRESS", l) is not None:
                tmap["ipv4_addresses"].append(val(l))
            elif re.match("IP4.GATEWAY:", l) is not None:
                tmap["ipv4_gw"] = val(l)
            elif re.match("IP4.DNS", l) is not None:
                v = val(l)
                if v is not None:
                    if v not in tmap["ipv4_dns"]:
                        tmap["ipv4_dns"].append(v)
            elif re.match("ipv4.dns:", l) is not None:
                v = val(l)
                if v is not None:
                    for ip in v.split(","):
                        if ip not in tmap["ipv4_dns"]:
                            tmap["ipv4_dns"].append(ip)
            elif re.match("ipv4.dns-search:", l) is not None:
                tmap["ipv4_dns_search"] = val(l)
            elif re.match("connection.type:", l) is not None:
                tmap["ctype"] = val(l)
                if tmap["ctype"] == "802-3-ethernet":
                    tmap[tmap["ctype"]] = {
                        "mac": None,
                        "cloned_mac": None,
                        "mtu": None,
                    }
                elif tmap["ctype"] in ("team", "bond"):
                    tmap[tmap["ctype"]] = {"config": None}
                elif tmap["ctype"] == "bridge":
                    cid = tmap["name"]
                    tmap[tmap["ctype"]] = {
                        "docker_name": None,
                        "aux_address": None,
                        "dgateway": None,
                        "host_binding": None,
                        "icc": False,
                        "internal": False,
                        "ip_masquerade": False,
                        "ip_range": None,
                        "subnet": None,
                    }
                    # Get docker_name
                    if docker_status():
                        # if (cid[0].startswith('br-')):  # custom-type docker network
                        if cid.startswith("br-"):  # custom-type docker network
                            docker_name = dname = dnets(cid[3:])[0]
                        else:  # default docker0 bridge network
                            docker_name = cid
                            dname = "bridge"
                        # Fill custom information, if any.
                        dtmap = dnet_inspect(dname)
                        tmap[tmap["ctype"]]["docker_name"] = docker_name
                        if dtmap["IPAM"]["Config"][0].get("AuxiliaryAddresses"):
                            tmap[tmap["ctype"]]["aux_address"] = parse_aux_addresses(
                                dtmap
                            )
                        # In some case, DNET inspect does NOT return Gateway in Docker version 18.09.5, build e8ff056
                        # This is likely related to the following bug in which the 'Gateway' is not reported the first
                        # time the docker daemon is started. Upon reload of docker daemon, it IS correctly reported.
                        # https://github.com/moby/moby/issues/26799
                        if dtmap["IPAM"]["Config"][0].get("Gateway"):
                            tmap[tmap["ctype"]]["dgateway"] = dtmap["IPAM"]["Config"][
                                0
                            ]["Gateway"]
                        if dtmap["Options"].get(
                            "com.docker.network.bridge.host_binding_ipv4"
                        ):
                            tmap[tmap["ctype"]]["host_binding"] = dtmap["Options"][
                                "com.docker.network.bridge.host_binding_ipv4"
                            ]
                        if dtmap["Options"].get("com.docker.network.bridge.enable_icc"):
                            tmap[tmap["ctype"]]["icc"] = to_boolean(
                                dtmap["Options"]["com.docker.network.bridge.enable_icc"]
                            )
                        tmap[tmap["ctype"]]["internal"] = dtmap["Internal"]
                        if dtmap["Options"].get(
                            "com.docker.network.bridge.ip_masquerade"
                        ):
                            tmap[tmap["ctype"]]["ip_masquerade"] = to_boolean(
                                dtmap["Options"][
                                    "com.docker.network.bridge.ip_masquerade"
                                ]
                            )
                            # if used com.docker.network.bridge.default_bridge may also
                            # requires to_boolean()
                        if dtmap["IPAM"]["Config"][0].get("IPRange"):
                            tmap[tmap["ctype"]]["ip_range"] = dtmap["IPAM"]["Config"][
                                0
                            ]["IPRange"]
                        tmap[tmap["ctype"]]["subnet"] = dtmap["IPAM"]["Config"][0][
                            "Subnet"
                        ]
                else:
                    tmap[tmap["ctype"]] = {}

            elif re.match("connection.master:", l) is not None:
                # for team, bond and bridge type connections.
                master = val(l)
                if master is not None:
                    tmap["master"] = master
            elif (
                re.match("802-3-ethernet.mac-address:", l) is not None
                and tmap["ctype"] == "802-3-ethernet"
            ):
                tmap[tmap["ctype"]]["mac"] = val(l)
            elif (
                re.match("802-3-ethernet.cloned-mac-address:", l) is not None
                and tmap["ctype"] == "802-3-ethernet"
            ):
                tmap[tmap["ctype"]]["cloned_mac"] = val(l)
            elif (
                re.match("802-3-ethernet.mtu:", l) is not None
                and tmap["ctype"] == "802-3-ethernet"
            ):
                tmap[tmap["ctype"]]["mtu"] = val(l)

            elif re.match("team.config:", l) is not None and tmap["ctype"] == "team":
                tmap[tmap["ctype"]]["config"] = l.split("team.config:")[1].strip()
            elif re.match("bond.options:", l) is not None and tmap["ctype"] == "bond":
                options = l.split("bond.options:")[1].strip()
                options_l = options.split("=")
                # @todo: there may be more options. for now, we just care about
                # mode.
                tmap[tmap["ctype"]]["config"] = json.dumps({options_l[0]: options_l[1]})
        tmap["ipv4_addresses"] = flatten(tmap["ipv4_addresses"])
        tmap["ipv4_dns"] = flatten(tmap["ipv4_dns"])
        cmap[uuid] = tmap
    return cmap


def valid_connection(uuid):
    o, e, rc = run_command([NMCLI, "c", "show", uuid], throw=False)
    if rc != 0:
        return False
    return True


def toggle_connection(uuid, switch):
    return run_command([NMCLI, "c", switch, uuid])


def delete_connection(uuid):
    if valid_connection(uuid):
        return run_command([NMCLI, "c", "delete", uuid])


def reload_connection(uuid):
    return run_command([NMCLI, "c", "reload", uuid])


def new_connection_helper(
    name, ipaddr, gateway, dns_servers, search_domains, mtu=DEFAULT_MTU
):
    manual = False
    if ipaddr is not None and len(ipaddr.strip()) > 0:
        manual = True
        run_command([NMCLI, "c", "mod", name, "ipv4.addresses", ipaddr])
    if gateway is not None and len(gateway.strip()) > 0:
        run_command([NMCLI, "c", "mod", name, "ipv4.gateway", gateway])
    if manual:
        run_command([NMCLI, "c", "mod", name, "ipv4.method", "manual"])

    if dns_servers is not None and len(dns_servers.strip()) > 0:
        run_command([NMCLI, "c", "mod", name, "ipv4.dns", dns_servers])
    if search_domains is not None and len(search_domains.strip()) > 0:
        run_command([NMCLI, "c", "mod", name, "ipv4.dns-search", search_domains])
    if mtu != DEFAULT_MTU:
        # no need to set it if it's default value
        run_command([NMCLI, "c", "mod", name, "802-3-ethernet.mtu", mtu])


def new_ethernet_connection(
    name,
    ifname,
    ipaddr=None,
    gateway=None,
    dns_servers=None,
    search_domains=None,
    mtu=DEFAULT_MTU,
):
    run_command(
        [NMCLI, "c", "add", "type", "ethernet", "con-name", name, "ifname", ifname]
    )
    new_connection_helper(name, ipaddr, gateway, dns_servers, search_domains, mtu=mtu)
    # @todo: probably better to get the uuid and reload with it instead of
    # name.
    reload_connection(name)


def new_member_helper(name, members, mtype):
    for i in range(len(members)):
        mname = "%s-slave-%d" % (name, i)
        run_command(
            [
                NMCLI,
                "c",
                "add",
                "type",
                mtype,
                "con-name",
                mname,
                "ifname",
                members[i],
                "master",
                name,
            ]
        )
    for i in range(len(members)):
        mname = "%s-slave-%d" % (name, i)
        run_command([NMCLI, "c", "up", mname])


# keeping new_team_connection and new_bond_connection separate even though they
# are very similar. We should consolidate after we are able to support all
# common config parameters in both modes.
def new_team_connection(
    name,
    config,
    members,
    ipaddr=None,
    gateway=None,
    dns_servers=None,
    search_domains=None,
    mtu=DEFAULT_MTU,
):
    run_command(
        [
            NMCLI,
            "c",
            "add",
            "type",
            "team",
            "con-name",
            name,
            "ifname",
            name,
            "config",
            config,
        ]
    )
    new_connection_helper(name, ipaddr, gateway, dns_servers, search_domains, mtu)
    new_member_helper(name, members, "team-slave")
    reload_connection(name)


def new_bond_connection(
    name,
    mode,
    members,
    ipaddr=None,
    gateway=None,
    dns_servers=None,
    search_domains=None,
):
    run_command(
        [
            NMCLI,
            "c",
            "add",
            "type",
            "bond",
            "con-name",
            name,
            "ifname",
            name,
            "mode",
            mode,
        ]
    )
    new_connection_helper(name, ipaddr, gateway, dns_servers, search_domains)
    new_member_helper(name, members, "bond-slave")
    reload_connection(name)


def enable_ip_forwarding(name: str, priority: int):
    """Enable IP forwarding
    Write a sysctl.d conf file and load it into sysctl configuration

    :type name: name of the conf file(s) to create
    :param priority: priority of the conf file(s) to create
    """
    out_fn = f"{SYSCTL_CONFD_PATH}{priority}-{name}.conf"
    logger.debug(f"Write sysctl.d conf file to enable IP forwarding: {out_fn}")
    try:
        with open(out_fn, "w") as f:
            f.write("net.ipv4.ip_forward = 1\n")
            f.write("net.ipv6.conf.all.forwarding = 1\n")
    except IOError as e:
        logger.exception(e)
        e_msg = (
            f"The sysctl configuration file couldn't be written to disk at {out_fn}."
        )
        raise IOError(e_msg)
    # Load into sysctl configuration
    cmd = [
        SYSCTL,
        "-p",
        f"{out_fn}",
    ]
    return run_command(cmd, log=True)


def disable_ip_forwarding(name: str):
    """Disable IP forwarding
    Find and delete the conf file with name matching the related service
    and manually set IP forwarding to 0 (as config reload is not enough).
    See https://github.com/rockstor/rockstor-core/issues/2679#issuecomment-1751421374
    """
    # Logic taken from https://docs.python.org/3.9/library/os.html#os.scandir
    with os.scandir(SYSCTL_CONFD_PATH) as it:
        for entry in it:
            if entry.name.endswith(f"{name}.conf") and entry.is_file():
                logger.debug(f"Delete {entry.path}")
                os.remove(entry.path)
    # Manually disable IP forwarding
    cmd = [
        SYSCTL,
        "-w",
        "net.ipv4.ip_forward=0",
        "-w",
        "net.ipv6.conf.all.forwarding=0",
    ]
    return run_command(cmd, log=True)
