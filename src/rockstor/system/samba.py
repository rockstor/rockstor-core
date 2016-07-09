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
import logging
from storageadmin.models import SambaCustomConfig
from django.conf import settings

logger = logging.getLogger(__name__)


TESTPARM = '/usr/bin/testparm'
SMB_CONFIG = '/etc/samba/smb.conf'
SYSTEMCTL = '/usr/bin/systemctl'
CHMOD = '/bin/chmod'
RS_HEADER = '####BEGIN: Rockstor SAMBA CONFIG####'


def test_parm(config='/etc/samba/smb.conf'):
    cmd = [TESTPARM, '-s', config]
    o, e, rc = run_command(cmd, throw=False)
    logger.debug('test_parm received rc of %s', rc)
    logger.debug('test_parm was passed %s', config)
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
    mnt_helper = os.path.join(settings.ROOT_DIR, 'bin/mnt-share')
    fo.write('%s\n' % RS_HEADER)
    for e in exports:
        admin_users = ''
        for au in e.admin_users.all():
            admin_users = '%s%s ' % (admin_users, au.username)
        fo.write('[%s]\n' % e.share.name)
        fo.write('    root preexec = "%s %s"\n' % (mnt_helper, e.share.name))
        fo.write('    root preexec close = yes\n')
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


def update_global_config(smb_config=None, ad_config=None):
    logger.debug('update_global_config called with smb_config = %s', smb_config)
    logger.debug('update_global_config called with ad_config = %s', ad_config)
    fh, npath = mkstemp()
    if (smb_config is None):
        smb_config = {}
    if (ad_config is not None):
        smb_config.update(ad_config)

    with open(SMB_CONFIG) as sfo, open(npath, 'w') as tfo:
        tfo.write('[global]\n')
        workgroup = smb_config.get('workgroup', 'MYGROUP')
        tfo.write('    workgroup = %s\n' % workgroup)
        smb_config.pop('workgroup', None)
        logfile = smb_config.get('log file', '/var/log/samba/log.%m')
        tfo.write('    log file = %s\n' % logfile)
        smb_config.pop('log file', None)
        if ('realm' in smb_config):
            idmap_high = int(smb_config['idmap_range'].split()[2])
            default_range = '%s - %s' % (idmap_high + 1, idmap_high + 1000000)
            tfo.write('    security = ads\n')
            tfo.write('    realm = %s\n' % smb_config['realm'])
            tfo.write('    template shell = /bin/sh\n')
            tfo.write('    kerberos method = secrets and keytab\n')
            tfo.write('    winbind use default domain = false\n')
            tfo.write('    winbind offline logon = true\n')
            tfo.write('    winbind enum users = yes\n')
            tfo.write('    winbind enum groups = yes\n')
            tfo.write('    idmap config * : backend = tdb\n')
            tfo.write('    idmap config * : range = %s\n' % default_range)
            # enable rfc2307 schema and collect UIDS from AD DC we assume if
            # rfc2307 then winbind nss info too - collects AD DC home and shell
            # for each user
            # TODO rfc2307 is now an unresolved reference
            if (rfc2307):
                tfo.write('    idmap config %s : backend = ad\n' % workgroup)
                tfo.write('    idmap config %s : range = %s\n' %
                          (workgroup, smb_config['idmap_range']))
                tfo.write('    idmap config %s : schema_mode = rfc2307\n' % workgroup)
                tfo.write('    winbind nss info = rfc2307\n')
            else:
                tfo.write('    idmap config %s : backend = rid\n' % workgroup)
                tfo.write('    idmap config %s : range = %s\n' % (workgroup, smb_config['idmap_range']))
            smb_config.pop('idmap_range', None)
        tfo.write('    log level = %s\n' % smb_config.get('log level', 3))
        smb_config.pop('log level', None)
        tfo.write('    load printers = %s\n' % smb_config.get('load printers', 'no'))
        smb_config.pop('load printers', None)
        tfo.write('    cups options = %s\n' % smb_config.get('cups options', 'raw'))
        smb_config.pop('cups options', None)
        tfo.write('    printcap name = %s\n' % smb_config.get('printcap name', '/dev/null'))
        smb_config.pop('printcap name', None)
        tfo.write('    map to guest = %s\n' % smb_config.get('map to guest', 'Bad User'))
        smb_config.pop('map to guest', None)

        for k in smb_config:
            tfo.write('    %s = %s\n' % (k, smb_config[k]))

        rockstor_section = False
        for line in sfo.readlines():
            if (re.match(RS_HEADER, line) is not None):
                rockstor_section = True
            if (rockstor_section is True):
                tfo.write(line)
    test_parm(npath)
    shutil.move(npath, SMB_CONFIG)

def get_global_config():
    config = {}
    with open(SMB_CONFIG) as sfo:
        global_section = False
        for l in sfo.readlines():
            if (re.match('\[global]', l) is not None):
                global_section = True
                continue
            if (not global_section or
                len(l.strip()) == 0 or
                re.match('#', l) is not None):
                continue
            if (global_section and
                re.match('\[', l) is not None):
                global_section = False
                continue
            fields = l.strip().split('=')
            logger.debug('FIELDS = %s', fields)
            logger.debug('LEN OF FIELDS = %s', len(fields))
            if len(fields) < 2:
                continue
            config[fields[0].strip()] = fields[1].strip()
    logger.debug('get_global_config returning %s', config)
    return config


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
