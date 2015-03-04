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

from system.osi import run_command
from django_ztask.decorators import task
from cli.rest_util import api_call
from system.services import service_status
from storageadmin.models import RockOn

DOCKER = '/usr/bin/docker'
ROCKON_URL = 'https://localhost/api/rockons'

import logging
logger = logging.getLogger(__name__)


def docker_status():
    o, e, rc = service_status('docker')
    if (rc != 0):
        return False
    return True


@task()
def start(rid):
    new_status = 'started'
    try:
        rockon = RockOn.objects.get(id=rid)
        if (rockon.name == 'Plex'):
            run_command([DOCKER, 'start', 'rockplex'])
    except:
        new_status = 'start_failed'
    finally:
        url = ('%s/%d/status_update' % (ROCKON_URL, rid))
        return api_call(url, data={'new_status': new_status, },
                        calltype='post', save_error=False)


@task()
def stop(rid):
    new_status = 'stopped'
    try:
        rockon = RockOn.objects.get(id=rid)
        if (rockon.name == 'Plex'):
            run_command([DOCKER, 'stop', 'rockplex'])
    except:
        new_status = 'stop_failed'
    finally:
        url = ('%s/%d/status_update' % (ROCKON_URL, rid))
        return api_call(url, data={'new_status': new_status, },
                        calltype='post', save_error=False)


@task()
def install(rid):
    new_state = 'installed'
    try:
        rockon = RockOn.objects.get(id=rid)
        if (rockon.name == 'Plex'):
            plex_install({'/mnt2/plex_config': '/config', })
    except Exception, e:
        logger.debug('exception while installing the rockon')
        logger.exception(e)
        new_state = 'install_failed'
    finally:
        url = ('%s/%d/state_update' % (ROCKON_URL, rid))
        return api_call(url, data={'new_state': new_state, }, calltype='post',
                        save_error=False)


@task()
def uninstall(rid):
    new_state = 'available'
    try:
        rockon = RockOn.objects.get(id=rid)
        if (rockon.name == 'Plex'):
            run_command([DOCKER, 'rm', 'rockplex'])
    except:
        new_state = 'error'
    finally:
        url = ('%s/%d/state_update' % (ROCKON_URL, rid))
        return api_call(url, data={'new_state': new_state, }, calltype='post',
                        save_error=False)


def plex_install(vol_map):
    pull_cmd = [DOCKER, 'pull', 'timhaak/plex', ]
    run_command(pull_cmd)
    cmd = [DOCKER, 'run', '-d', '--name', 'rockplex', '--net="host"', ]
    config_share = None
    for v in vol_map:
        if (vol_map[v] == '/config'):
            config_share = v
        cmd.extend(['-v', '%s:%s' % (v, vol_map[v]), ])
    cmd.extend(['-p', '32400:32400', 'timhaak/plex', ])
    run_command(cmd)
    run_command([DOCKER, 'stop', 'rockplex', ])
    pref_file = ('%s/Library/Application Support/Plex Media Server/'
                 'Preferences.xml' % config_share)
    import re
    from tempfile import mkstemp
    from shutil import move
    fo, npath = mkstemp()
    with open(pref_file) as pfo, open(npath, 'w') as tfo:
        for l in pfo.readlines():
            nl = l
            if (re.match('<Preferences ', l) is not None):
                nl = ('%s allowedNetworks="192.168.56.0/255.255.255.0"/>' %
                      l[:-3])
            tfo.write('%s\n' % nl)
    return move(npath, pref_file)


def ovpn_bootstrap():
    #volume container
    volc_cmd = [DOCKER, 'run', '--name', 'ovpn-data', '-v', '/etc/openvpn',
                'busybox', ]
    run_command(volc_cmd)
    #initialize vol container data
    dinit_cmd = [DOCKER, 'run', '--volumes-from', 'ovpn-data', '--rm',
                 'kylemanna/openvpn', 'ovpn_genconfig', '-u',
                 'udp://localhost', ]
    run_command(dinit_cmd)
