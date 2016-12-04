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

import os
import shutil
from system.osi import (run_command, md5sum)
from system import services
import logging
import sys
import re
import time
import json
from tempfile import mkstemp
from django.conf import settings
from system.pkg_mgmt import downgrade_pkgs


logger = logging.getLogger(__name__)

SYSCTL = '/usr/bin/systemctl'
BASE_DIR = settings.ROOT_DIR
BASE_BIN = '%sbin' % BASE_DIR
DJANGO = '%s/django' % BASE_BIN
STAMP = '%s/.initrock' % BASE_DIR
FLASH_OPTIMIZE = '%s/flash-optimize' % BASE_BIN
PREP_DB = '%s/prep_db' % BASE_BIN
SUPERCTL = '%s/supervisorctl' % BASE_BIN
OPENSSL = '/usr/bin/openssl'
GRUBBY = '/usr/sbin/grubby'
RPM = '/usr/bin/rpm'
YUM = '/usr/bin/yum'


def delete_old_kernels(logging, num_retain=5):
    #Don't keep more than num_retain kernels
    o, e, rc = run_command([RPM, '-q', 'kernel-ml'])
    ml_kernels = o[:-1] #last entry is an empty string.
    ml_kernels = sorted(ml_kernels)
    #centos kernels, may or may not be installed.
    centos_kernels = []
    o, e, rc = run_command([RPM, '-q', 'kernel'], throw=False)
    if (rc == 0): centos_kernels = o[:-1]

    #Don't delete current running kernel
    #Don't delete current default kernel
    running_kernel = os.uname()[2]
    default_kernel = settings.SUPPORTED_KERNEL_VERSION
    deleted = 0
    for k in centos_kernels:
        kv = k.split('kernel-')[1]
        if (kv != running_kernel and
            kv != default_kernel):
            run_command([YUM, 'remove', '-y', k])
            deleted += 1
            logging.info('Deleted old Kernel: %s' % k)
    for i in range(len(centos_kernels) + len(ml_kernels) - deleted - num_retain):
        kv = ml_kernels[i].split('kernel-ml-')[1]
        if (kv != running_kernel and
            kv != default_kernel):
            run_command([YUM, 'remove', '-y', ml_kernels[i]])
            logging.info('Deleted old Kernel: %s' % ml_kernels[i])


def init_update_issue():
    from smart_manager.models import Service
    from storageadmin.models import NetworkConnection
    ipaddr = None
    so = Service.objects.get(name='rockstor')
    if (so.config is not None):
        config = json.loads(so.config)
        try:
            ipaddr = NetworkConnection.objects.get(name=config['network_interface']).ipaddr
        except NetworkConnection.DoesNotExist:
            pass
    if (ipaddr is None):
        default_if = None
        some_if = None

        o, e, c = run_command(['/usr/sbin/route'])
        for i in o:
            if (len(i.strip()) == 0):
                continue
            if (re.match('default', i) is not None):
                default_if = i.split()[-1]
            else:
                some_if = i.split()[-1]
        if (default_if is None):
            default_if = some_if
        if (default_if is not None):
            o2, e, c = run_command(['/usr/sbin/ifconfig', default_if])
            for i2 in o2:
                if (re.match('inet ', i2.strip()) is not None):
                    ipaddr = i2.split()[1]

    with open('/etc/issue', 'w') as ifo:
        if (ipaddr is None):
            ifo.write('The system does not yet have an ip address.\n')
            ifo.write('Rockstor cannot be configured using the web interface '
                        'without this.\n\n')
            ifo.write('Press Enter to receive updated network status\n')
            ifo.write('If this message persists please login as root and configure '
                      'your network using nmtui, then reboot.\n')
        else:
            ifo.write('\nRockstor is successfully installed.\n\n')
            ifo.write('You can access the web-ui by pointing your browser to '
                      'https://%s\n\n' % ipaddr)
    return ipaddr


def update_nginx(logger):
    try:
        #importing here because, APIWrapper needs postgres to be setup, so
        #importing at the top results in failure the first time.
        from smart_manager.models import Service
        from storageadmin.models import NetworkConnection
        ip = None
        port = 443
        so = Service.objects.get(name='rockstor')
        if (so.config is not None):
            config = json.loads(so.config)
            port = config['listener_port']
            try:
                ip = NetworkConnection.objects.get(name=config['network_interface']).ipaddr
            except NetworkConnection.DoesNotExist:
                logger.error('Network interface(%s) configured for rockstor '
                             'service does not exist' % config['network_interface'])
                return
        services.update_nginx(ip, port)
    except Exception, e:
        logger.error('Exception occured while trying to update nginx')
        logger.exception(e)


def set_def_kernel(logger, version=settings.SUPPORTED_KERNEL_VERSION):
    supported_kernel_path = ('/boot/vmlinuz-%s' % version)
    if (not os.path.isfile(supported_kernel_path)):
        return logger.error('Supported kernel(%s) does not exist' %
                            supported_kernel_path)
    try:
        o, e, rc = run_command([GRUBBY, '--default-kernel'])
        if (o[0] == supported_kernel_path):
            return logging.info('Supported kernel(%s) is already the default' %
                                supported_kernel_path)
    except Exception, e:
        return logger.error('Exception while listing the default kernel: %s'
                            % e.__str__())

    try:
        run_command([GRUBBY, '--set-default=%s' % supported_kernel_path])
        return logger.info('Default kernel set to %s' % supported_kernel_path)
    except Exception, e:
        return logger.error('Exception while setting kernel(%s) as default: %s' %
                            (version, e.__str__()))

def update_tz(logging):
    # update timezone variable in settings.py
    zonestr = os.path.realpath('/etc/localtime').split('zoneinfo/')[1]
    logging.info('system timezone = %s' % zonestr)
    sfile = '%s/src/rockstor/settings.py' % BASE_DIR
    fo, npath = mkstemp()
    updated = False
    with open(sfile) as sfo, open(npath, 'w') as tfo:
        for line in sfo.readlines():
            if (re.match('TIME_ZONE = ', line) is not None):
                curzone = line.strip().split('= ')[1].strip("'")
                if (curzone == zonestr):
                    break
                else:
                    tfo.write("TIME_ZONE = '%s'\n" % zonestr)
                    updated = True
                    logging.info('Changed timezone from %s to %s' %
                                 (curzone, zonestr))
            else:
                tfo.write(line)
    if (updated):
        shutil.move(npath, sfile)
    else:
        os.remove(npath)
    return updated

def bootstrap_sshd_config(logging):
    # Set AllowUsers if needed
    with open('/etc/ssh/sshd_config', 'a+') as sfo:
        found = False
        for line in sfo.readlines():
            if (re.match(settings.SSHD_HEADER, line) is not None or
                re.match('AllowUsers ', line) is not None):
                # if header is found,
                found = True
                logging.info('sshd_config already has the updates.'
                             ' Leaving it unchanged.')
                break
        if (not found):
            sfo.write('%s\n' % settings.SSHD_HEADER)
            sfo.write('AllowUsers root\n')
            logging.info('updated sshd_config')
            run_command([SYSCTL, 'restart', 'sshd'])

def require_postgres(logging):
    rs_dest = '/etc/systemd/system/rockstor-pre.service'
    rs_src = '%s/conf/rockstor-pre.service' % BASE_DIR
    logging.info('updating rockstor-pre service..')
    with open(rs_dest, 'w') as dfo, open(rs_src) as sfo:
        for l in sfo.readlines():
            dfo.write(l)
            if (re.match('After=postgresql.service', l) is not None):
                dfo.write('Requires=postgresql.service\n')
                logging.info('rockstor-pre now requires postgresql')
    run_command([SYSCTL, 'daemon-reload'])
    return logging.info('systemd daemon reloaded')

def enable_rockstor_service(logging):
    rs_dest = '/etc/systemd/system/rockstor.service'
    rs_src = '%s/conf/rockstor.service' % BASE_DIR
    sum1 = md5sum(rs_dest)
    sum2 = md5sum(rs_src)
    if (sum1 != sum2):
        logging.info('updating rockstor systemd service')
        shutil.copy(rs_src, rs_dest)
        run_command([SYSCTL, 'enable', 'rockstor'])
        logging.info('Done.')
    logging.info('rockstor service looks correct. Not updating.')

def enable_bootstrap_service(logging):
    name = 'rockstor-bootstrap.service'
    bs_dest = '/etc/systemd/system/%s' % name
    bs_src = ('%s/conf/%s' % (BASE_DIR, name))
    sum1 = "na"
    if (os.path.isfile(bs_dest)):
        sum1 = md5sum(bs_dest)
    sum2 = md5sum(bs_src)
    if (sum1 != sum2):
        logging.info('updating rockstor-bootstrap systemd service')
        shutil.copy(bs_src, bs_dest)
        run_command([SYSCTL, 'enable', name])
        run_command([SYSCTL, 'daemon-reload'])
        return logging.info('Done.')
    return logging.info('%s looks correct. Not updating.' % name)

def update_smb_service(logging):
    name = 'smb.service'
    ss_dest = '/etc/systemd/system/%s' % name
    if (not os.path.isfile(ss_dest)):
        return logging.info('%s is not enabled. Not updating.')
    ss_src = '%s/conf/%s' % (BASE_DIR, name)
    sum1 = md5sum(ss_dest)
    sum2 = md5sum(ss_src)
    if (sum1 != sum2):
        logging.info('Updating %s' % name)
        shutil.copy(ss_src, ss_dest)
        run_command([SYSCTL, 'daemon-reload'])
        return logging.info('Done.')
    return logging.info('%s looks correct. Not updating.' % name)

def cleanup_rclocal(logging):
    #this could potentially be problematic if users want to have a custom
    #rc.local file, which is not really needed or recommended due to better
    #systemd alternative method.

    #This cleanup method can be safely removed when we know there are no
    #<3.8-9 versions out there any more.

    rc_dest = '/etc/rc.d/rc.local'
    rc_src = '%s/conf/rc.local' % BASE_DIR
    sum1 = md5sum(rc_dest)
    sum2 = md5sum(rc_src)
    if (sum1 != sum2):
        logging.info('updating %s' % rc_dest)
        shutil.copy(rc_src, rc_dest)
        logging.info('Done.')
        return os.chmod(rc_dest, 0755)
    logging.info('%s looks correct. Not updating.' % rc_dest)

def downgrade_python(logging):
    #With the release of CentOS 7.2, the new python package(2.7.5-34)
    #backported some questionable changes that break gevent. So we downgrade to
    #previous version: 2.7.5-18. I've moved these packages to rockrepo for
    #now. Once the frankenversion resolves itself, we'll remove this workaround.
    o, e, rc = run_command([YUM, 'info', 'python'])
    for l in o:
        if (re.match('Release.*34.el7$', l) is not None):
            logging.info('Downgrading python and python-libs')
            return downgrade_pkgs('python-2.7.5-18.el7_1.1', 'python-libs-2.7.5-18.el7_1.1')

def main():
    loglevel = logging.INFO
    if (len(sys.argv) > 1 and sys.argv[1] == '-x'):
        loglevel = logging.DEBUG
    logging.basicConfig(format='%(asctime)s: %(message)s', level=loglevel)
    set_def_kernel(logging)
    try:
        delete_old_kernels(logging)
    except Exception, e:
        logging.debug('Exception while deleting old kernels. Soft error. Moving on.')
        logging.exception(e)

    cert_loc = '%s/certs/' % BASE_DIR
    if (os.path.isdir(cert_loc)):
        if (not os.path.isfile('%s/rockstor.cert' % cert_loc) or
            not os.path.isfile('%s/rockstor.key' % cert_loc)):
            shutil.rmtree(cert_loc)

    if (not os.path.isdir(cert_loc)):
        os.mkdir(cert_loc)
        dn = ("/C=US/ST=Rockstor user's state/L=Rockstor user's "
              "city/O=Rockstor user/OU=Rockstor dept/CN=rockstor.user")
        logging.info('Creating openssl cert...')
        run_command([OPENSSL, 'req', '-nodes', '-newkey', 'rsa:2048',
                     '-keyout', '%s/first.key' % cert_loc, '-out',
                     '%s/rockstor.csr' % cert_loc, '-subj', dn])
        logging.debug('openssl cert created')
        logging.info('Creating rockstor key...')
        run_command([OPENSSL, 'rsa', '-in', '%s/first.key' % cert_loc, '-out',
                     '%s/rockstor.key' % cert_loc])
        logging.debug('rockstor key created')
        logging.info('Singing cert with rockstor key...')
        run_command([OPENSSL, 'x509', '-in', '%s/rockstor.csr' % cert_loc,
                     '-out', '%s/rockstor.cert' % cert_loc, '-req', '-signkey',
                     '%s/rockstor.key' % cert_loc, '-days', '3650'])
        logging.debug('cert signed.')
        logging.info('restarting nginx...')
        run_command([SUPERCTL, 'restart', 'nginx'])

    cleanup_rclocal(logging)
    logging.info('Checking for flash and Running flash optimizations if appropriate.')
    run_command([FLASH_OPTIMIZE, '-x'], throw=False)
    tz_updated = False
    try:
        logging.info('Updating the timezone from the system')
        tz_updated = update_tz(logging)
    except Exception, e:
        logging.error('Exception while updating timezone: %s' % e.__str__())
        logging.exception(e)

    try:
        logging.info('Updating sshd_config')
        bootstrap_sshd_config(logging)
    except Exception, e:
        logging.error('Exception while updating sshd_config: %s' % e.__str__())

    if (not os.path.isfile(STAMP)):
        logging.info('Please be patient. This script could take a few minutes')
        shutil.copyfile('%s/conf/django-hack' % BASE_DIR,
                        '%s/django' % BASE_BIN)
        run_command([SYSCTL, 'enable', 'postgresql'])
        logging.debug('Progresql enabled')
        pg_data = '/var/lib/pgsql/data'
        if (os.path.isdir(pg_data)):
            shutil.rmtree('/var/lib/pgsql/data')
        logging.info('initializing Postgresql...')
        run_command(['/usr/bin/postgresql-setup', 'initdb'])
        logging.info('Done.')
        run_command([SYSCTL, 'restart', 'postgresql'])
        run_command([SYSCTL, 'status', 'postgresql'])
        logging.debug('Postgresql restarted')
        logging.info('Creating app databases...')
        run_command(['su', '-', 'postgres', '-c', '/usr/bin/createdb smartdb'])
        logging.debug('smartdb created')
        run_command(['su', '-', 'postgres', '-c',
                     '/usr/bin/createdb storageadmin'])
        logging.debug('storageadmin created')
        logging.info('Done')
        logging.info('Initializing app databases...')
        run_command(['su', '-', 'postgres', '-c', "psql -c \"CREATE ROLE rocky WITH SUPERUSER LOGIN PASSWORD 'rocky'\""])
        logging.debug('rocky ROLE created')
        run_command(['su', '-', 'postgres', '-c', "psql storageadmin -f %s/conf/storageadmin.sql.in" % BASE_DIR])
        logging.debug('storageadmin app database loaded')
        run_command(['su', '-', 'postgres', '-c', "psql smartdb -f %s/conf/smartdb.sql.in" % BASE_DIR])
        logging.debug('smartdb app database loaded')
        logging.info('Done')
        run_command(['cp', '-f', '%s/conf/postgresql.conf' % BASE_DIR,
                     '/var/lib/pgsql/data/'])
        logging.debug('postgresql.conf copied')
        run_command(['cp', '-f', '%s/conf/pg_hba.conf' % BASE_DIR,
                     '/var/lib/pgsql/data/'])
        logging.debug('pg_hba.conf copied')
        run_command([SYSCTL, 'restart', 'postgresql'])
        logging.info('Postgresql restarted')
        logging.info('Running app database migrations...')
        migration_cmd = [DJANGO, 'migrate', '--noinput',]
        fake_migration_cmd = migration_cmd + ['--fake']
        smartdb_opts = ['--database=smart_manager', 'smart_manager']
        run_command(fake_migration_cmd + ['storageadmin', '0001_initial'])
        run_command(fake_migration_cmd + smartdb_opts + ['0001_initial'])
        run_command(migration_cmd + ['storageadmin'])
        run_command(migration_cmd + smartdb_opts)
        run_command(migration_cmd + ['auth'])
        run_command(migration_cmd + ['django_ztask'])
        logging.info('Done')
        logging.info('Running prepdb...')
        run_command([PREP_DB, ])
        logging.info('Done')
        run_command(['touch', STAMP])
        require_postgres(logging)
        logging.info('Done')
    else:
        logging.info('Running prepdb...')
        run_command([PREP_DB, ])


    logging.info('stopping firewalld...')
    run_command([SYSCTL, 'stop', 'firewalld'])
    run_command([SYSCTL, 'disable', 'firewalld'])
    logging.info('firewalld stopped and disabled')
    update_nginx(logging)
    try:
        #downgrading python is a stopgap until it's fixed in upstream.
        downgrade_python(logging)
    except Exception, e:
        logging.error('Exception while downgrading python: %s' % e.__str__())
        logging.exception(e)

    shutil.copyfile('/etc/issue', '/etc/issue.rockstor')
    for i in range(30):
        try:
            if (init_update_issue() is not None):
                # init_update_issue() didn't cause an exception and did return
                # an ip so we break out of the multi try loop as we are done.
                break
            else:
                # execute except block with message so we can try again.
                raise Exception('default interface IP not yet configured')
        except Exception, e:
            # only executed if there is an actual exception with
            # init_update_issue() or if it returns None so we can try again
            # regardless as in both instances we may succeed on another try.
            logging.debug('Exception occurred while running update_issue: %s. '
                         'Trying again after 2 seconds.' % e.__str__())
            if (i > 28):
                logging.error('Waited too long and tried too many times. '
                              'Quiting.')
                raise e
            time.sleep(2)

    enable_rockstor_service(logging)
    enable_bootstrap_service(logging)

if __name__ == '__main__':
    main()
