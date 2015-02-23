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

DOCKER = '/usr/bin/docker'
ROCKON_URL = 'https://localhost/api/rockons'


def docker_status():
    o, e, rc = service_status('docker')
    if (rc != 0):
        return False
    return True


@task()
def start(rid):
    new_status = 'started'
    try:
        cmd = [DOCKER, 'ps', ]
        run_command(cmd)
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
        cmd = [DOCKER, 'ps', ]
        run_command(cmd)
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
        cmd = [DOCKER, 'ps', ]
        run_command(cmd)
    except:
        new_state = 'install_failed'
    finally:
        url = ('%s/%d/state_update' % (ROCKON_URL, rid))
        return api_call(url, data={'new_state': new_state, }, calltype='post',
                        save_error=False)


@task()
def uninstall(rid):
    new_state = 'available'
    try:
        cmd = [DOCKER, 'ps', ]
        run_command(cmd)
    except:
        new_state = 'error'
    finally:
        url = ('%s/%d/state_update' % (ROCKON_URL, rid))
        return api_call(url, data={'new_state': new_state, }, calltype='post',
                        save_error=False)
