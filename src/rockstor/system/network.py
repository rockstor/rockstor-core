"""
Copyright (c) 2012-2013 RockStor, Inc. <http://rockstor.com>
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

import re
from osi import run_command


NMCLI = '/usr/bin/nmcli'

def val(s):
    fields = s.split(': ')
    if (len(fields) < 2):
        return None
    v = fields[1].strip()
    if (len(v) == 0 or v == '--'):
        return None
    return v


def devices():
    dmap = {}
    o, e, rc = run_command([NMCLI, '-t', '-f', 'device', 'device'])
    for dev in o:
        if (len(dev.strip()) == 0):
            continue
        tmap = {
            'dtype': None,
            'mac': None,
            'mtu': None,
            'state': None,
        }
        o2, e2, r2 = run_command([NMCLI, 'd', 'show', dev])
        for l in o2:
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


def connections():
    cmap = {}
    o, e, rc = run_command([NMCLI, '-t', '-f', 'uuid', 'c', 'show', ])

    def flatten(l):
        s = ','.join(l)
        if (len(s) == 0):
            return None
        return s

    for uuid in o:
        if (len(uuid.strip()) == 0):
            continue
        tmap = {'name': None,
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
        cmd = [NMCLI, 'c', 'show', uuid]
        o2, e2, rc2 = run_command([NMCLI, 'c', 'show', uuid,])
        for l in o2:
            if (re.match('ipv4.method:', l) is not None):
                tmap['ipv4_method'] = val(l)
            elif (re.match('GENERAL.NAME:', l) is not None):
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
                else:
                    tmap[tmap['ctype']] = {}

            elif (re.match('connection.master:', l) is not None):
                #for team, bond and bridge type connections.
                master = val(l)
                if (master is not None):
                    tmap['master'] = master
            elif (re.match('802-3-ethernet.mac-address:', l) is not None
                  and '802-3-ethernet' in tmap):
                tmap['802-3-ethernet']['mac'] = val(l)
            elif (re.match('802-3-ethernet.cloned-mac-address:', l) is not None
                  and '802-3-ethernet' in tmap):
                tmap['802-3-ethernet']['cloned_mac'] = val(l)
            elif (re.match('802-3-ethernet.mtu:', l) is not None
                  and '802-3-ethernet' in tmap):
                tmap['802-3-ethernet']['mtu'] = val(l)

        tmap['ipv4_addresses'] = flatten(tmap['ipv4_addresses'])
        tmap['ipv4_dns'] = flatten(tmap['ipv4_dns'])
        cmap[uuid] = tmap
    return cmap
