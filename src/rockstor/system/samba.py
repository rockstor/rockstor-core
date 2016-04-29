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
RS_HEADER = '####BEGIN: Rockstor SAMBA CONFIG####'


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
    fo.write('%s\n' % RS_HEADER)
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
        if (e.shadow_copy):
            fo.write('    shadow:format = .' + e.snapshot_prefix + '_%Y%m%d%H%M\n')
            fo.write('    shadow:basedir = %s\n' % e.path)
            fo.write('    shadow:snapdir = ./\n')
            fo.write('    shadow:sort = desc\n')
            fo.write('    vfs objects = shadow_copy2\n')
            fo.write('    veto files = /.%s*/\n' % e.snapshot_prefix)
        for cco in SambaCustomConfig.objects.filter(smb_share=e):
            if (cco.custom_config.strip()):
                    fo.write('    %s\n' % cco.custom_config)
    fo.write('####END: Rockstor SAMBA CONFIG####\n')


def refresh_smb_config(exports):
    fh, npath = mkstemp()
    with open(SMB_CONFIG) as sfo, open(npath, 'w') as tfo:
        rockstor_section = False
        for line in sfo.readlines():
            if (re.match(RS_HEADER, line)
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


def update_global_config(workgroup=None, realm=None, idmap_range=None, rfc2307=False):
    fh, npath = mkstemp()
    with open(SMB_CONFIG) as sfo, open(npath, 'w') as tfo:
        tfo.write('[global]\n')
        if (workgroup is not None):
            tfo.write('    workgroup = %s\n' % workgroup)
        tfo.write('    log file = /var/log/samba/log.%m\n')
        if (realm is not None):
            idmap_high = int(idmap_range.split()[2])
            default_range = '%s - %s' % (idmap_high + 1, idmap_high + 1000000)
            tfo.write('    security = ads\n')
            tfo.write('    realm = %s\n' % realm)
            tfo.write('    template shell = /bin/sh\n')
            tfo.write('    kerberos method = secrets and keytab\n')
            tfo.write('    winbind use default domain = false\n')
            tfo.write('    winbind offline logon = true\n')
            tfo.write('    winbind enum users = yes\n')
            tfo.write('    winbind enum groups = yes\n')
            tfo.write('    idmap config * : backend = tdb\n')
            tfo.write('    idmap config * : range = %s\n' % default_range)
            #enable rfc2307 schema and collect UIDS from AD DC
            #we assume if rfc2307 then winbind nss info too - collects AD DC home and shell for each user 
            if (rfc2307):
                tfo.write('    idmap config %s : backend = ad\n' % workgroup)
                tfo.write('    idmap config %s : range = %s\n' % (workgroup, idmap_range))
                tfo.write('    idmap config %s : schema_mode = rfc2307\n' % workgroup)
                tfo.write('    winbind nss info = rfc2307\n')
            else:
                tfo.write('    idmap config %s : backend = rid\n' % workgroup)
                tfo.write('    idmap config %s : range = %s\n' % (workgroup, idmap_range))
        #@todo: remove log level once AD integration is working well for users.
        tfo.write('    log level = 3\n')
        tfo.write('    load printers = no\n')
        tfo.write('    cups options = raw\n')
        tfo.write('    printcap name = /dev/null\n\n')

        rockstor_section = False
        for line in sfo.readlines():
            if (re.match(RS_HEADER, line) is not None):
                rockstor_section = True
            if (rockstor_section is True):
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
