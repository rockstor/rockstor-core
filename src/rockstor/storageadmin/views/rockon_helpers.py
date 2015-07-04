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

import time
from system.osi import run_command
from django.conf import settings
from django_ztask.decorators import task
from cli.rest_util import api_call
from system.services import service_status
from storageadmin.models import (RockOn, DContainer, DVolume, DPort,
                                 DCustomConfig, Share, Disk, DContainerLink,
                                 ContainerOption)
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
    ro = RockOn.objects.get(name=name)
    state = 'unknown error'
    co = DContainer.objects.filter(rockon=ro).order_by('-launch_order')[0]
    try:
        o, e, rc = run_command([DOCKER, 'inspect', '-f',
                                '{{range $key, $value := .State}}{{$key}}:{{$value}},{{ end }}', co.name])
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
    o, e, rc = run_command([DOCKER, 'stop', name], throw=False)
    o, e, rc = run_command([DOCKER, 'rm', name], throw=False)
    return logger.debug('Attempted to remove a container(%s). out: %s '
                        'err: %s rc: %s.' %  (name, o, e, rc))

@task()
def start(rid):
    new_status = 'started'
    try:
        rockon = RockOn.objects.get(id=rid)
        for c in DContainer.objects.filter(rockon=rockon).order_by('launch_order'):
            run_command([DOCKER, 'start', c.name])
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
        for c in DContainer.objects.filter(rockon=rockon).order_by('-launch_order'):
            run_command([DOCKER, 'stop', c.name])
    except Exception, e:
        logger.debug('exception while stopping the rockon(%s)' % rid)
        logger.exception(e)
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
        pull_images(rockon)
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
        elif (rockon.name == 'OwnCloud'):
            owncloud_install(rockon)
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
        for c in DContainer.objects.filter(rockon=rockon):
            rm_container(c.name)
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
            share_mnt = '%s%s' % (settings.MNT_PT, v.share.name)
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


def container_ops(container):
    ops_list = []
    for o in ContainerOption.objects.filter(container=container):
        ops_list.append(o.name)
        if (len(o.val.strip()) > 0):
            ops_list.append(o.val)
    return ops_list


def port_ops(container):
    ops_list = []
    for po in DPort.objects.filter(container=container):
        pstr = '%s:%s' % (po.hostp, po.containerp)
        if (po.protocol is not None):
            pstr = '%s/%s' % (pstr, po.protocol)
        ops_list.extend(['-p', pstr])
    return ops_list

def vol_ops(container):
    ops_list = []
    for v in DVolume.objects.filter(container=container):
        share_mnt = ('%s%s' % (settings.MNT_PT, v.share.name))
        ops_list.extend(['-v', '%s:%s' % (share_mnt, v.dest_dir)])
    return ops_list

def ovpn_install(rockon):
    #volume container
    vol_co = DContainer.objects.get(rockon=rockon, launch_order=1)
    volc_cmd = [DOCKER, 'run', '--name', vol_co.name,]
    volc_cmd.extend(container_ops(vol_co))
    volc_cmd.append(vol_co.dimage.name)
    run_command(volc_cmd)
    #initialize vol container data
    cco = DCustomConfig.objects.get(rockon=rockon)
    oc = DContainer.objects.get(rockon=rockon, launch_order=2)
    dinit_cmd = [DOCKER, 'run', '--rm',]
    dinit_cmd.extend(container_ops(oc))
    dinit_cmd.extend([oc.dimage.name, 'ovpn_genconfig', '-u', 'udp://%s' % cco.val, ])
    run_command(dinit_cmd)
    #start the server
    server_cmd = [DOCKER, 'run', '-d', '--name', oc.name,]
    server_cmd.extend(container_ops(oc))
    server_cmd.extend(port_ops(oc))
    server_cmd.append(oc.dimage.name)
    run_command(server_cmd)


def transmission_install(rockon):
    rm_container(rockon.name)
    cmd = [DOCKER, 'run', '-d', '--name', rockon.name,]
    for cco in DCustomConfig.objects.filter(rockon=rockon):
        cmd.extend(['-e', '%s=%s' % (cco.key, cco.val)])
    c = DContainer.objects.get(rockon=rockon)
    image = c.dimage.name
    run_command([DOCKER, 'pull', image])
    for v in DVolume.objects.filter(container=c):
        share_mnt = '%s%s' % (settings.MNT_PT, v.share.name)
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
        share_mnt = '%s%s' % (settings.MNT_PT, v.share.name)
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
        share_mnt = '%s%s' % (settings.MNT_PT, v.share.name)
        mount_share(v.share.name, share_mnt)
        cmd.extend(['-v', '%s:%s' % (share_mnt, v.dest_dir), ])
    for p in DPort.objects.filter(container=c):
        cmd.extend(['-p', '%d:%d' % (p.hostp, p.containerp), ])
    cmd.append(image)
    run_command(cmd)


def pull_images(rockon):
    for c in DContainer.objects.filter(rockon=rockon):
        rm_container(c.name)
        run_command([DOCKER, 'pull', c.dimage.name])

def owncloud_install(rockon):
    for c in DContainer.objects.filter(rockon=rockon).order_by('launch_order'):
        cmd = [DOCKER, 'run', '-d', '--name', c.name, ]
        db_user = DCustomConfig.objects.get(rockon=rockon, key='db_user').val
        db_pw = DCustomConfig.objects.get(rockon=rockon, key='db_pw').val
        if (c.dimage.name == 'postgres'):
            cmd.extend(['-e', 'POSTGRES_USER=%s' % db_user, '-e',
                        'POSTGRES_PASSWORD=%s' % db_pw])
        cmd.extend(port_ops(c))
        for lo in DContainerLink.objects.filter(destination=c):
            cmd.extend(['--link', '%s:%s' % (lo.source.name, lo.name)])
        cmd.extend(vol_ops(c))
        if (c.name == 'owncloud'):
            cmd.extend(['-v', '%s/rockstor.key:/etc/ssl/private/owncloud.key' % settings.CERTDIR,
                        '-v', '%s/rockstor.cert:/etc/ssl/certs/owncloud.crt' % settings.CERTDIR,
                        '-e', 'HTTPS_ENABLED=true'])
            cmd.extend(['-e', 'DB_USER=%s' % db_user, '-e', 'DB_PASS=%s' % db_pw,])
        cmd.append(c.dimage.name)
        logger.debug('docker cmd = %s' % cmd)
        run_command(cmd)
        if (c.dimage.name == 'postgres'):
            #make sure postgres is setup
            cur_wait = 0;
            while (True):
                o, e, rc = run_command([DOCKER, 'exec', c.name, 'psql', '-U',
                                        'postgres', '-c', "\l"], throw=False)
                if (rc == 0):
                    break
                if (cur_wait > 300):
                    logger.error('Waited too long(300 seconds) for '
                                 'postgres to initialize for owncloud. giving up.')
                    break
                time.sleep(1)
                cur_wait += 1
