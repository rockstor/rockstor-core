"""
Copyright (c) 2012-2019 RockStor, Inc. <http://rockstor.com>
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

import json
import logging
import re

from .exceptions import CommandException
from .osi import run_command


NMCLI = '/usr/bin/nmcli'
DEFAULT_MTU = 1500
logger = logging.getLogger(__name__)


def val(s):
    fields = s.split(': ')
    if (len(fields) < 2):
        return None
    v = fields[1].strip()
    if (len(v) == 0 or v == '--'):
        return None
    return v


def get_dev_list():
    """
    Returns a list of connection devices as seen by Network Manager
    :return: list
    """
    o, e, rc = run_command([NMCLI, '-t', '-f', 'device', 'device'])
    return o


def get_dev_config(dev_list):
    """
    Takes a list of connection devices and returns a dictionary with
    each device's config as seens by Network Manager
    :param dev_list: list returned by get_dev_list()
    :return: dictionary
    """
    dmap = {}
    for dev in dev_list:
        if (len(dev.strip()) == 0):
            continue
        tmap = {
            'dtype': None,
            'mac': None,
            'mtu': None,
            'state': None,
        }
        try:
            o, e, r = run_command([NMCLI, 'd', 'show', dev])
        except CommandException as e:
            # especially veth devices can vanish abruptly sometimes.
            if e.rc == 10:
                logger.exception(e)
                logger.debug('device: {} vanished. Discarding it'.format(dev))
                continue
            raise

        for l in o:
            if (re.match('GENERAL.TYPE:', l) is not None):
                tmap['dtype'] = val(l)
            elif (re.match('GENERAL.HWADDR:', l) is not None):
                tmap['mac'] = val(l)
            elif (re.match('GENERAL.MTU:', l) is not None):
                tmap['mtu'] = val(l)
            elif (re.match('GENERAL.STATE:', l) is not None):
                tmap['state'] = val(l)
            elif (re.match('GENERAL.CONNECTION:', l) is not None):
                connection = val(l)
                if (connection is not None):
                    tmap['connection'] = connection
        dmap[dev] = tmap
    return dmap


def get_con_list():
    """
    Returns a list of connections as seen by Network Manager.
    :return: list
    """
    o, e, rc = run_command([NMCLI, '-t', '-f', 'uuid', 'c', 'show', ])
    return o


def get_con_config(con_list):
    """
    Takes a list of connections and returns a dictionary with
    each connection's config as seens by Network Manager
    :param con_list: list returned by get_con_list()
    :return: dictionary
    """
    cmap = {}

    def flatten(l):
        s = ','.join(l)
        if (len(s) == 0):
            return None
        return s

    for uuid in con_list:
        if (len(uuid.strip()) == 0):
            continue
        tmap = {
            'name': None,
            'state': None,
            'ipv4_method': None,
            'ipv4_addresses': [],
            'ipv4_gw': None,
            'ipv4_dns': [],
            'ipv4_dns_search': None,
            'ipv6_method': None,
            'ipv6_addresses': None,
            'ipv6_gw': None,
            'ipv6_dns': None,
            'ipv6_dns_search': None,
        }
        try:
            o, e, rc = run_command([NMCLI, 'c', 'show', uuid, ])
        except CommandException as e:
            # in case the connection disappears
            if e.rc == 10:
                logger.exception(e)
                logger.debug('connection: {} vanished. Discarding it'.format(
                    uuid))
                continue
            raise e
        for l in o:
            if (re.match('ipv4.method:', l) is not None):
                tmap['ipv4_method'] = val(l)
            elif (re.match('connection.id:', l) is not None):
                tmap['name'] = val(l)
            elif (re.match('GENERAL.STATE:', l) is not None):
                tmap['state'] = val(l)
            elif (re.match('IP4.ADDRESS', l) is not None):
                tmap['ipv4_addresses'].append(val(l))
            elif (re.match('IP4.GATEWAY:', l) is not None):
                tmap['ipv4_gw'] = val(l)
            elif (re.match('IP4.DNS', l) is not None):
                v = val(l)
                if (v is not None):
                    if (v not in tmap['ipv4_dns']):
                        tmap['ipv4_dns'].append(v)
            elif (re.match('ipv4.dns:', l) is not None):
                v = val(l)
                if (v is not None):
                    for ip in v.split(','):
                        if (ip not in tmap['ipv4_dns']):
                            tmap['ipv4_dns'].append(ip)
            elif (re.match('ipv4.dns-search:', l) is not None):
                tmap['ipv4_dns_search'] = val(l)
            elif (re.match('connection.type:', l) is not None):
                tmap['ctype'] = val(l)
                if (tmap['ctype'] == '802-3-ethernet'):
                    tmap[tmap['ctype']] = {
                        'mac': None,
                        'cloned_mac': None,
                        'mtu': None,
                    }
                elif (tmap['ctype'] in ('team', 'bond')):
                    tmap[tmap['ctype']] = {
                        'config': None
                    }
                else:
                    tmap[tmap['ctype']] = {}

            elif (re.match('connection.master:', l) is not None):
                # for team, bond and bridge type connections.
                master = val(l)
                if (master is not None):
                    tmap['master'] = master
            elif (re.match('802-3-ethernet.mac-address:', l) is not None and
                  tmap['ctype'] == '802-3-ethernet'):
                tmap[tmap['ctype']]['mac'] = val(l)
            elif (re.match('802-3-ethernet.cloned-mac-address:', l) is not
                  None and tmap['ctype'] == '802-3-ethernet'):
                tmap[tmap['ctype']]['cloned_mac'] = val(l)
            elif (re.match('802-3-ethernet.mtu:', l) is not None and
                  tmap['ctype'] == '802-3-ethernet'):
                tmap[tmap['ctype']]['mtu'] = val(l)

            elif (re.match('team.config:', l) is not None and
                  tmap['ctype'] == 'team'):
                tmap[tmap['ctype']]['config'] = l.split(
                    'team.config:')[1].strip()
            elif (re.match('bond.options:', l) is not None and
                  tmap['ctype'] == 'bond'):
                options = l.split('bond.options:')[1].strip()
                options_l = options.split('=')
                # @todo: there may be more options. for now, we just care about
                # mode.
                tmap[tmap['ctype']]['config'] = json.dumps(
                    {options_l[0]: options_l[1]})
        tmap['ipv4_addresses'] = flatten(tmap['ipv4_addresses'])
        tmap['ipv4_dns'] = flatten(tmap['ipv4_dns'])
        cmap[uuid] = tmap
    return cmap


def valid_connection(uuid):
    o, e, rc = run_command([NMCLI, 'c', 'show', uuid], throw=False)
    if (rc != 0):
        return False
    return True


def toggle_connection(uuid, switch):
    return run_command([NMCLI, 'c', switch, uuid])


def delete_connection(uuid):
    if (valid_connection(uuid)):
        return run_command([NMCLI, 'c', 'delete', uuid])


def reload_connection(uuid):
    return run_command([NMCLI, 'c', 'reload', uuid])


def new_connection_helper(name, ipaddr, gateway, dns_servers, search_domains,
                          mtu=DEFAULT_MTU):
    manual = False
    if (ipaddr is not None and len(ipaddr.strip()) > 0):
        manual = True
        run_command([NMCLI, 'c', 'mod', name, 'ipv4.addresses', ipaddr])
    if (gateway is not None and len(gateway.strip()) > 0):
        run_command([NMCLI, 'c', 'mod', name, 'ipv4.gateway', gateway])
    if (manual):
        run_command([NMCLI, 'c', 'mod', name, 'ipv4.method', 'manual'])

    if (dns_servers is not None and len(dns_servers.strip()) > 0):
        run_command([NMCLI, 'c', 'mod', name, 'ipv4.dns', dns_servers])
    if (search_domains is not None and len(search_domains.strip()) > 0):
        run_command([NMCLI, 'c', 'mod', name, 'ipv4.dns-search',
                     search_domains])
    if (mtu != DEFAULT_MTU):
        # no need to set it if it's default value
        run_command([NMCLI, 'c', 'mod', name, '802-3-ethernet.mtu', mtu])


def new_ethernet_connection(name, ifname, ipaddr=None, gateway=None,
                            dns_servers=None, search_domains=None,
                            mtu=DEFAULT_MTU):
    run_command([NMCLI, 'c', 'add', 'type', 'ethernet', 'con-name', name,
                 'ifname', ifname])
    new_connection_helper(name, ipaddr, gateway, dns_servers, search_domains,
                          mtu=mtu)
    # @todo: probably better to get the uuid and reload with it instead of
    # name.
    reload_connection(name)


def new_member_helper(name, members, mtype):
    for i in range(len(members)):
        mname = '%s-slave-%d' % (name, i)
        run_command([NMCLI, 'c', 'add', 'type', mtype, 'con-name', mname,
                     'ifname', members[i], 'master', name])
    for i in range(len(members)):
        mname = '%s-slave-%d' % (name, i)
        run_command([NMCLI, 'c', 'up', mname])


# keeping new_team_connection and new_bond_connection separate even though they
# are very similar. We should consolidate after we are able to support all
# common config parameters in both modes.
def new_team_connection(name, config, members, ipaddr=None, gateway=None,
                        dns_servers=None, search_domains=None,
                        mtu=DEFAULT_MTU):
    run_command([NMCLI, 'c', 'add', 'type', 'team', 'con-name', name, 'ifname',
                 name, 'config', config])
    new_connection_helper(name, ipaddr, gateway, dns_servers, search_domains,
                          mtu)
    new_member_helper(name, members, 'team-slave')
    reload_connection(name)


def new_bond_connection(name, mode, members, ipaddr=None, gateway=None,
                        dns_servers=None, search_domains=None):
    run_command([NMCLI, 'c', 'add', 'type', 'bond', 'con-name', name, 'ifname',
                 name, 'mode', mode])
    new_connection_helper(name, ipaddr, gateway, dns_servers, search_domains)
    new_member_helper(name, members, 'bond-slave')
    reload_connection(name)
