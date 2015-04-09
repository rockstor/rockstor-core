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
from storageadmin.models import (RockOn, DContainer, DVolume, DPort,
                                 DCustomConfig)

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
        run_command([DOCKER, 'start', rockon.name])
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
        run_command([DOCKER, 'stop', rockon.name])
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
            plex_install(rockon)
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
            run_command([DOCKER, 'rm', rockon.name, ])
    except:
        new_state = 'error'
    finally:
        url = ('%s/%d/state_update' % (ROCKON_URL, rid))
        return api_call(url, data={'new_state': new_state, }, calltype='post',
                        save_error=False)


def plex_install(rockon):
    cmd = [DOCKER, 'run', '-d', '--name', rockon.name, '--net="host"', ]
    config_share = None
    for c in DContainer.objects.filter(rockon=rockon):
        image = c.dimage.name
        run_command([DOCKER, 'pull', image, ])
        for v in DVolume.objects.filter(container=c):
            share_mnt = '/mnt2/%s' % v.share.name
            if (v.dest_dir == '/config'):
                config_share = share_mnt
            cmd.extend(['-v', '%s:%s' % (share_mnt, v.dest_dir), ])
        for p in DPort.objects.filter(container=c):
            cmd.extend(['-p', '%d:%d' % (p.hostp, p.containerp), ])
        cmd.append(image)
    logger.debug('cmd = %s' % cmd)
    run_command(cmd)
    run_command([DOCKER, 'stop', rockon.name, ])
    pref_file = ('%s/Library/Application Support/Plex Media Server/'
                 'Preferences.xml' % config_share)
    logger.debug('pref file: %s' % pref_file)
    cco = DCustomConfig.objects.get(rockon=rockon)
    logger.debug('network val %s' % cco.val)
    import re
    from tempfile import mkstemp
    from shutil import move
    fo, npath = mkstemp()
    with open(pref_file) as pfo, open(npath, 'w') as tfo:
        for l in pfo.readlines():
            nl = l
            if (re.match('<Preferences ', l) is not None and
                re.match('allowedNetworks', l) is None):
                nl = ('%s allowedNetworks="%s"/>' %
                      (l[:-3], cco.val))
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
