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
                                 DCustomConfig, Share, Disk)
from fs import btrfs

DOCKER = '/usr/bin/docker'
ROCKON_URL = 'https://localhost/api/rockons'

import logging
logger = logging.getLogger(__name__)


def docker_status():
    o, e, rc = service_status('docker')
    if (rc != 0):
        return False
    return True

def mount_share(name, mnt):
    share = Share.objects.get(name=name)
    disk = Disk.objects.filter(pool=share.pool)[0].name
    btrfs.mount_share(share, disk, mnt)

def rockon_status(name):
    state = 'unknown error'
    try:
        o, e, rc = run_command([DOCKER, 'inspect', '-f', '{{range $key, $value := .State}}{{$key}}:{{$value}},{{ end }}', name])
        state_d = {}
        for i in o[0].split(','):
            fields = i.split(':')
            if (len(fields) >= 2):
                state_d[fields[0]] = ':'.join(fields[1:])
        if ('Running' in state_d):
            if (state_d['Running'] == 'true'):
                state = 'started'
            else:
                state = 'stopped'
                if ('Error' in state_d and 'ExitCode' in state_d):
                    exitcode = int(state_d['ExitCode'])
                    if (exitcode != 0):
                        state = 'exitcode: %d error: %s' % (exitcode, state_d['Error'])
        return state
    except Exception, e:
        logger.exception(e)
    finally:
        return state


def rm_container(name):
    o, e, rc = run_command([DOCKER, 'rm', name], throw=False)
    return logger.debug('Attempted to remove a container(%s). out: %s '
                        'err: %s rc: %s.' %  (name, o, e, rc))

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
def update(rid):
    uninstall(rid, new_state='pending_update')
    install(rid)


@task()
def install(rid):
    new_state = 'installed'
    try:
        rockon = RockOn.objects.get(id=rid)
        if (rockon.name == 'Plex'):
            plex_install(rockon)
        elif (rockon.name == 'OpenVPN'):
            ovpn_install(rockon)
        elif (rockon.name == 'Transmission'):
            transmission_install(rockon)
        elif (rockon.name == 'BTSync'):
            btsync_install(rockon)
        elif (rockon.name == 'Syncthing'):
            syncthing_install(rockon)
    except Exception, e:
        logger.debug('exception while installing the rockon')
        logger.exception(e)
        new_state = 'install_failed'
    finally:
        url = ('%s/%d/state_update' % (ROCKON_URL, rid))
        return api_call(url, data={'new_state': new_state, }, calltype='post',
                        save_error=False)


@task()
def uninstall(rid, new_state='available'):
    try:
        rockon = RockOn.objects.get(id=rid)
        rm_container(rockon.name)
        if (rockon.name == 'OpenVPN'):
            rm_container('ovpn-data')
    except Exception, e:
        logger.debug('exception while uninstalling rockon')
        logger.exception(e)
        new_state = 'uninstall_failed'
    finally:
        url = ('%s/%d/state_update' % (ROCKON_URL, rid))
        return api_call(url, data={'new_state': new_state, }, calltype='post',
                        save_error=False)


def plex_install(rockon):
    # to make install idempotent, remove the container that may exist from a previous attempt
    rm_container(rockon.name)
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


def ovpn_install(rockon):
    rm_container('ovpn-data')
    rm_container(rockon.name)
    cco = DCustomConfig.objects.get(rockon=rockon)
    for c in DContainer.objects.filter(rockon=rockon):
        image = c.dimage.name
        run_command([DOCKER, 'pull', image, ])
    oc = DContainer.objects.get(rockon=rockon, name='openvpn')
    po = DPort.objects.get(container=oc)
    data_container = 'ovpn-data'
    image = 'kylemanna/openvpn'
    logger.debug('server name = %s' % cco.val)
    #volume container
    volc_cmd = [DOCKER, 'run', '--name', data_container, '-v', '/etc/openvpn',
                'busybox', ]
    run_command(volc_cmd)
    logger.debug('volume container initialized')
    #initialize vol container data
    dinit_cmd = [DOCKER, 'run', '--volumes-from', data_container, '--rm',
                 image, 'ovpn_genconfig', '-u', 'udp://%s' % cco.val, ]
    run_command(dinit_cmd)
    #logger.debug('volume container initialized 2')
    #dinit2_cmd = [DOCKER, 'run', '--volumes-from', data_container, '--rm', '-it', image, 'ovpn_initpki', ]
    #run_command(dini(t2_cmd)
    logger.debug('volume container initialized 3')
    server_cmd = [DOCKER, 'run', '--volumes-from', data_container, '-d', '--name', rockon.name,
                  '-p', '%s:%s/udp' % (po.hostp, po.containerp), '--cap-add=NET_ADMIN', image]
    run_command(server_cmd)
    run_command([DOCKER, 'stop', rockon.name])


def transmission_install(rockon):
    rm_container(rockon.name)
    cmd = [DOCKER, 'run', '-d', '--name', rockon.name,]
    for cco in DCustomConfig.objects.filter(rockon=rockon):
        cmd.extend(['-e', '%s=%s' % (cco.key, cco.val)])
    c = DContainer.objects.get(rockon=rockon)
    image = c.dimage.name
    run_command([DOCKER, 'pull', image])
    for v in DVolume.objects.filter(container=c):
        share_mnt = '/mnt2/%s' % v.share.name
        mount_share(v.share.name, share_mnt)
        cmd.extend(['-v', '%s:%s' % (share_mnt, v.dest_dir), ])
    for p in DPort.objects.filter(container=c):
        cmd.extend(['-p', '%d:%d' % (p.hostp, p.containerp), ])
    cmd.append(image)
    run_command(cmd)


def btsync_install(rockon):
    rm_container(rockon.name)
    cmd = [DOCKER, 'run', '-d', '--name', rockon.name,]
    c = DContainer.objects.get(rockon=rockon)
    image = c.dimage.name
    run_command([DOCKER, 'pull', image])
    for v in DVolume.objects.filter(container=c):
        share_mnt = '/mnt2/%s' % v.share.name
        mount_share(v.share.name, share_mnt)
        cmd.extend(['-v', '%s:%s' % (share_mnt, v.dest_dir), ])
    for p in DPort.objects.filter(container=c):
        cmd.extend(['-p', '%d:%d' % (p.hostp, p.containerp), ])
    cmd.append(image)
    run_command(cmd)


def syncthing_install(rockon):
    rm_container(rockon.name)
    cmd = [DOCKER, 'run', '-d', '--name', rockon.name,]
    c = DContainer.objects.get(rockon=rockon)
    image = c.dimage.name
    run_command([DOCKER, 'pull', image])
    for v in DVolume.objects.filter(container=c):
        share_mnt = '/mnt2/%s' % v.share.name
        mount_share(v.share.name, share_mnt)
        cmd.extend(['-v', '%s:%s' % (share_mnt, v.dest_dir), ])
    for p in DPort.objects.filter(container=c):
        cmd.extend(['-p', '%d:%d' % (p.hostp, p.containerp), ])
    cmd.append(image)
    run_command(cmd)
