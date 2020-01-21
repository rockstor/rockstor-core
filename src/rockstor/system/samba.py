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
from django.conf import settings


TESTPARM = '/usr/bin/testparm'
SMB_CONFIG = '/etc/samba/smb.conf'
SYSTEMCTL = '/usr/bin/systemctl'
CHMOD = '/usr/bin/chmod'
RS_SHARES_HEADER = '####BEGIN: Rockstor SAMBA CONFIG####'
RS_SHARES_FOOTER = '####END: Rockstor SAMBA CONFIG####'
RS_AD_HEADER = '####BEGIN: Rockstor ACTIVE DIRECTORY CONFIG####'
RS_AD_FOOTER = '####END: Rockstor ACTIVE DIRECTORY CONFIG####'
RS_CUSTOM_HEADER = '####BEGIN: Rockstor SAMBA GLOBAL CUSTOM####'
RS_CUSTOM_FOOTER = '####END: Rockstor SAMBA GLOBAL CUSTOM####'


def test_parm(config='/etc/samba/smb.conf'):
    cmd = [TESTPARM, '-s', config]
    o, e, rc = run_command(cmd, throw=False)
    if (rc != 0):
        raise Exception('Syntax error while checking the temporary '
                        'samba config file')
    return True


def rockstor_smb_config(fo, exports):
    mnt_helper = os.path.join(settings.ROOT_DIR, 'bin/mnt-share')
    fo.write('%s\n' % RS_SHARES_HEADER)
    for e in exports:
        admin_users = ''
        for au in e.admin_users.all():
            admin_users = '%s%s ' % (admin_users, au.username)
        fo.write('[%s]\n' % e.share.name)
        fo.write('    root preexec = "%s %s"\n' % (mnt_helper, e.share.name))
        fo.write('    root preexec close = yes\n')
        fo.write('    comment = %s\n' % e.comment.encode('utf-8'))
        fo.write('    path = %s\n' % e.path)
        fo.write('    browseable = %s\n' % e.browsable)
        fo.write('    read only = %s\n' % e.read_only)
        fo.write('    guest ok = %s\n' % e.guest_ok)
        if (len(admin_users) > 0):
            fo.write('    admin users = %s\n' % admin_users)
        if (e.shadow_copy):
            fo.write('    shadow:format = .' + e.snapshot_prefix + '_%Y%m%d%H%M\n')  # noqa E501
            fo.write('    shadow:basedir = %s\n' % e.path)
            fo.write('    shadow:snapdir = ./\n')
            fo.write('    shadow:sort = desc\n')
            fo.write('    shadow:localtime = yes\n')
            fo.write('    vfs objects = shadow_copy2\n')
            fo.write('    veto files = /.%s*/\n' % e.snapshot_prefix)
        for cco in SambaCustomConfig.objects.filter(smb_share=e):
            if (cco.custom_config.strip()):
                fo.write('    %s\n' % cco.custom_config)
    fo.write('%s\n' % RS_SHARES_FOOTER)


def refresh_smb_config(exports):
    fh, npath = mkstemp()
    with open(SMB_CONFIG) as sfo, open(npath, 'w') as tfo:
        rockstor_section = False
        for line in sfo.readlines():
            if (re.match(RS_SHARES_HEADER, line) is not None):
                rockstor_section = True
                rockstor_smb_config(tfo, exports)
                break
            else:
                tfo.write(line)
        if (rockstor_section is False):
            rockstor_smb_config(tfo, exports)
    test_parm(npath)
    shutil.move(npath, SMB_CONFIG)


# write out new [global] section and re-write the existing rockstor section.
def update_global_config(smb_config=None, ad_config=None):
    fh, npath = mkstemp()
    if (smb_config is None):
        smb_config = {}

    with open(SMB_CONFIG) as sfo, open(npath, 'w') as tfo:
        # Start building samba [global] section with base config
        tfo.write('[global]\n')

        # Write some defaults samba params
        # only if not passed via samba custom config
        smb_default_options = {
            'log file': '/var/log/samba/log.%m',
            'log level': 3,
            'load printers': 'no',
            'cups options': 'raw',
            'printcap name': '/dev/null',
            'map to guest': 'Bad User'
        }
        for key, value in smb_default_options.iteritems():
            if key not in smb_config:
                tfo.write('    %s = %s\n' % (key, value))

        # Fill samba [global] section with our custom samba params
        # before updating smb_config dict with AD data to avoid
        # adding non samba params like AD username and password
        if (smb_config is not None):
            tfo.write('\n%s\n' % RS_CUSTOM_HEADER)
            for k in smb_config:
                if (ad_config is not None and k == 'workgroup'):
                    tfo.write('    %s = %s\n' % (k, ad_config[k]))
                    continue
                tfo.write('    %s = %s\n' % (k, smb_config[k]))
            tfo.write('%s\n\n' % RS_CUSTOM_FOOTER)

        # Next add AD config to smb_config and build AD section
        if (ad_config is not None):
            smb_config.update(ad_config)

        domain = smb_config.pop('domain', None)
        if (domain is not None):
            idmap_high = int(smb_config['idmap_range'].split()[2])
            default_range = '%s - %s' % (idmap_high + 1, idmap_high + 1000000)
            workgroup = ad_config['workgroup']
            tfo.write('%s\n' % RS_AD_HEADER)
            tfo.write('    security = ads\n')
            tfo.write('    realm = %s\n' % domain)
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
            if (smb_config.pop('rfc2307', None)):
                tfo.write('    idmap config %s : backend = ad\n' % workgroup)
                tfo.write('    idmap config %s : range = %s\n' %
                          (workgroup, smb_config['idmap_range']))
                tfo.write('    idmap config %s : schema_mode = rfc2307\n'
                          % workgroup)
                tfo.write('    winbind nss info = rfc2307\n')
            else:
                tfo.write('    idmap config %s : backend = rid\n' % workgroup)
                tfo.write('    idmap config %s : range = %s\n' %
                          (workgroup, smb_config['idmap_range']))
            tfo.write('%s\n\n' % RS_AD_FOOTER)

        # After default [global], custom [global] and AD writes
        # finally add smb shares
        rockstor_section = False
        for line in sfo.readlines():
            if (re.match(RS_SHARES_HEADER, line) is not None):
                rockstor_section = True
            if (rockstor_section is True):
                tfo.write(line)
    test_parm(npath)
    shutil.move(npath, SMB_CONFIG)


def get_global_config():
    # start with config as None so it will return null elsewhere
    # if no fields are added to it.
    config = None
    with open(SMB_CONFIG) as sfo:
        global_section = False
        global_custom_section = False
        for l in sfo.readlines():
            # Check one, entering smb.conf [global] section
            if (re.match('\[global]', l) is not None):
                global_section = True
                continue
            # Check two, entering Rockstor custome params section under
            # [global]
            if (re.match(RS_CUSTOM_HEADER, l) is not None):
                global_custom_section = True
                continue
            if ((global_custom_section and
                 re.match(RS_CUSTOM_FOOTER, l) is not None)):
                global_custom_section = False
                continue
            # we ignore lines outside [global], empty lines, or
            # commends(starting with # or ;)
            if ((not global_section or
                 not global_custom_section or
                 len(l.strip()) == 0 or
                 re.match('#', l) is not None or
                 re.match(';', l) is not None)):
                continue
            if (global_section and re.match('\[', l) is not None):
                global_section = False
                continue
            fields = l.strip().split(' = ')
            if len(fields) < 2:
                continue
            # reset config to a usable dictionary since we're about to add
            # something to it
            if(config is None):
                config = {}
            config[fields[0].strip()] = fields[1].strip()
    # return our config variable, which is either None, or a dictionary with
    # fields inside of it
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
