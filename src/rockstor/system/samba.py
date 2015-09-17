"""
Copyright (c) 2012-2014 RockStor, Inc. <http://rockstor.com>
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

from osi import run_command
from services import service_status
import shutil
from tempfile import mkstemp
import re
import os
from storageadmin.models import SambaCustomConfig

TESTPARM = '/usr/bin/testparm'
SMB_CONFIG = '/etc/samba/smb.conf'
SYSTEMCTL = '/usr/bin/systemctl'
CHMOD = '/bin/chmod'


def test_parm(config='/etc/samba/smb.conf'):
    cmd = [TESTPARM, '-s', config]
    o, e, rc = run_command(cmd, throw=False)
    if (rc != 0):
        try:
            os.remove(npath)
        except:
            pass
        finally:
            raise Exception('Syntax error while checking the temporary '
                            'samba config file')
    return True


def rockstor_smb_config(fo, exports):
    fo.write('####BEGIN: Rockstor SAMBA CONFIG####\n')
    for e in exports:
        admin_users = ''
        for au in e.admin_users.all():
            admin_users = '%s%s ' % (admin_users, au.username)
        fo.write('[%s]\n' % e.share.name)
        fo.write('    comment = %s\n' % e.comment)
        fo.write('    path = %s\n' % e.path)
        fo.write('    browseable = %s\n' % e.browsable)
        fo.write('    read only = %s\n' % e.read_only)
        fo.write('    guest ok = %s\n' % e.guest_ok)
        if (len(admin_users) > 0):
            fo.write('    admin users = %s\n' % admin_users)
        if (e.shadow_copy == 'yes'):
            fo.write('    shadow:format = .hourly_%Y%m%d%H%M\n')
            fo.write('    shadow:basedir = %s\n' % e.path)
            fo.write('    shadow:snapdir = ./\n')
            fo.write('    shadow:sort = desc\n')
            fo.write('    vfs objects = shadow_copy2\n')
            fo.write('    veto files = /.hourly*/\n')
        for cco in SambaCustomConfig.objects.filter(smb_share=e):
            if (cco.custom_config.strip()):
                    fo.write('    %s\n' % cco.custom_config)
    fo.write('####END: Rockstor SAMBA CONFIG####\n')


def refresh_smb_config(exports):
    fh, npath = mkstemp()
    with open(SMB_CONFIG) as sfo, open(npath, 'w') as tfo:
        rockstor_section = False
        for line in sfo.readlines():
            if (re.match('####BEGIN: Rockstor SAMBA CONFIG####', line)
                is not None):
                rockstor_section = True
                rockstor_smb_config(tfo, exports)
                break
            else:
                tfo.write(line)
        if (rockstor_section is False):
            rockstor_smb_config(tfo, exports)
    test_parm(npath)
    shutil.move(npath, SMB_CONFIG)


def update_global_config(workgroup):
    fh, npath = mkstemp()
    with open(SMB_CONFIG) as sfo, open(npath, 'w') as tfo:
        for line in sfo.readlines():
            if (re.match('workgroup = ', line.strip()) is not None):
                line = 'workgroup = %s\n' % workgroup
            tfo.write(line)
    test_parm(npath)
    shutil.move(npath, SMB_CONFIG)


def restart_samba(hard=False):
    """
    call whenever config is updated
    """
    mode = 'reload'
    if (hard):
        mode = 'restart'
    run_command([SYSTEMCTL, mode, 'smb'])
    return run_command([SYSTEMCTL, mode, 'nmb'])

def update_samba_discovery():
    avahi_smb_config = '/etc/avahi/services/smb.service'
    if (os.path.isfile(avahi_smb_config)):
        os.remove(avahi_smb_config)
    return run_command([SYSTEMCTL, 'restart', 'avahi-daemon', ])


def status():
    return service_status('smb')
