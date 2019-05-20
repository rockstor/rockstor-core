"""
Copyright (c) 2012-2017 RockStor, Inc. <http://rockstor.com>
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
import json
from tempfile import mkstemp
from django.conf import settings


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
IP = '/usr/sbin/ip'


def delete_old_kernels(logging, num_retain=5):
    # Don't keep more than num_retain kernels
    o, e, rc = run_command([RPM, '-q', 'kernel-ml'])
    ml_kernels = o[:-1]  # last entry is an empty string.
    ml_kernels = sorted(ml_kernels)
    # centos kernels, may or may not be installed.
    centos_kernels = []
    o, e, rc = run_command([RPM, '-q', 'kernel'], throw=False)
    if (rc == 0):
        centos_kernels = o[:-1]

    # Don't delete current running kernel
    # Don't delete current default kernel
    running_kernel = os.uname()[2]
    default_kernel = settings.SUPPORTED_KERNEL_VERSION
    deleted = 0
    for k in centos_kernels:
        kv = k.split('kernel-')[1]
        if (kv != running_kernel and kv != default_kernel):
            run_command([YUM, 'remove', '-y', k])
            deleted += 1
            logging.info('Deleted old Kernel: %s' % k)
    for i in range(len(centos_kernels) + len(ml_kernels) - deleted -
                   num_retain):
        kv = ml_kernels[i].split('kernel-ml-')[1]
        if (kv != running_kernel and kv != default_kernel):
            run_command([YUM, 'remove', '-y', ml_kernels[i]])
            logging.info('Deleted old Kernel: %s' % ml_kernels[i])


def inet_addrs(interface=None):
    cmd = [IP, 'addr', 'show']
    if interface is not None:
        cmd.append(interface)
    o, _, _ = run_command(cmd)
    ipaddr_list = []
    for l in o:
        if (re.match('inet ', l.strip()) is not None):
            inet_fields = l.split()
            if len(inet_fields) > 1:
                ip_fields = inet_fields[1].split('/')
                if len(ip_fields) == 2:
                    ipaddr_list.append(ip_fields[0])
    return ipaddr_list


def current_rockstor_mgmt_ip(logger):
    # importing here because, APIWrapper needs postgres to be setup, so
    # importing at the top results in failure the first time.
    from smart_manager.models import Service

    ipaddr = None
    port = 443
    so = Service.objects.get(name='rockstor')

    if so.config is not None:
        config = json.loads(so.config)
        port = config['listener_port']
        try:
            ipaddr_list = inet_addrs(config['network_interface'])
            if len(ipaddr_list) > 0:
                ipaddr = ipaddr_list[0]
        except Exception as e:
            # interface vanished.
            logger.exception('Exception while gathering current management '
                             'ip: {e}'.format(e=e))

    return ipaddr, port


def init_update_issue(logger):
    ipaddr, port = current_rockstor_mgmt_ip(logger)

    if ipaddr is None:
        ipaddr_list = inet_addrs()

    with open('/etc/issue', 'w') as ifo:
        if (ipaddr is None and len(ipaddr_list) == 0):
            ifo.write('The system does not yet have an ip address.\n')
            ifo.write('Rockstor cannot be configured using the web interface '
                      'without this.\n\n')
            ifo.write('Press Enter to receive updated network status\n')
            ifo.write('If this message persists please login as root and '
                      'configure your network using nmtui, then reboot.\n')
        else:
            ifo.write('\nRockstor is successfully installed.\n\n')
            if ipaddr is not None:
                port_str = ''
                if port != 443:
                    port_str = ':{0}'.format(port)
                ifo.write('web-ui is accessible with this link: '
                          'https://{0}{1}\n\n'.format(ipaddr, port_str))
            else:
                ifo.write('web-ui is accessible with the following links:\n')
                for i in ipaddr_list:
                    ifo.write('https://{0}\n'.format(i))
    return ipaddr


def update_nginx(logger):
    try:
        ip, port = current_rockstor_mgmt_ip(logger)
        services.update_nginx(ip, port)
    except Exception as e:
        logger.exception('Exception while updating nginx: {e}'.format(e=e))


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
    except Exception as e:
        return logger.error('Exception while listing the default kernel: %s'
                            % e.__str__())

    try:
        run_command([GRUBBY, '--set-default=%s' % supported_kernel_path])
        return logger.info('Default kernel set to %s' % supported_kernel_path)
    except Exception as e:
        return logger.error('Exception while setting kernel(%s) as '
                            'default: %s' % (version, e.__str__()))


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


def main():
    loglevel = logging.INFO
    if (len(sys.argv) > 1 and sys.argv[1] == '-x'):
        loglevel = logging.DEBUG
    logging.basicConfig(format='%(asctime)s: %(message)s', level=loglevel)
    set_def_kernel(logging)
    try:
        delete_old_kernels(logging)
    except Exception as e:
        logging.debug('Exception while deleting old kernels. Soft error. '
                      'Moving on.')
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

    logging.info('Checking for flash and Running flash optimizations if '
                 'appropriate.')
    run_command([FLASH_OPTIMIZE, '-x'], throw=False)
    try:
        logging.info('Updating the timezone from the system')
        update_tz(logging)
    except Exception as e:
        logging.error('Exception while updating timezone: %s' % e.__str__())
        logging.exception(e)

    try:
        logging.info('Updating sshd_config')
        bootstrap_sshd_config(logging)
    except Exception as e:
        logging.error('Exception while updating sshd_config: %s' % e.__str__())

    if (not os.path.isfile(STAMP)):
        logging.info('Please be patient. This script could take a few minutes')
        shutil.copyfile('%s/conf/django-hack' % BASE_DIR,
                        '%s/django' % BASE_BIN)
        run_command([SYSCTL, 'enable', 'postgresql'])
        logging.debug('Progresql enabled')
        pg_data = '/var/lib/pgsql/data'
        if (os.path.isdir(pg_data)):
            logger.debug('Deleting /var/lib/pgsql/data')
            shutil.rmtree('/var/lib/pgsql/data')
        logging.info('initializing Postgresql...')
        # Conditionally run this only if found (CentOS/RedHat script)
        if os.path.isfile('/usr/bin/postgresql-setup'):
            logger.debug('running postgresql-setup initdb')
            # Legacy (CentOS) db init command
            run_command(['/usr/bin/postgresql-setup', 'initdb'])
        else:
            ## In eg openSUSE run the generic initdb from postgresql##-server
            if os.path.isfile('/usr/bin/initdb'):
                logger.debug('running generic initdb on {}'.format(pg_data))
                run_command(
                    ['su', '-', 'postgres', '-c', '/usr/bin/initdb -D {}'.format(pg_data)])
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
        run_command(['su', '-', 'postgres', '-c', "psql -c \"CREATE ROLE rocky WITH SUPERUSER LOGIN PASSWORD 'rocky'\""])  # noqa E501
        logging.debug('rocky ROLE created')
        run_command(['su', '-', 'postgres', '-c', "psql storageadmin -f %s/conf/storageadmin.sql.in" % BASE_DIR])  # noqa E501
        logging.debug('storageadmin app database loaded')
        run_command(['su', '-', 'postgres', '-c',
                     "psql smartdb -f %s/conf/smartdb.sql.in" % BASE_DIR])
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
        run_command(['touch', STAMP])
        require_postgres(logging)
        logging.info('Done')

    logging.info('Running app database migrations...')
    migration_cmd = [DJANGO, 'migrate', '--noinput', ]
    fake_migration_cmd = migration_cmd + ['--fake']
    fake_initial_migration_cmd = migration_cmd + ['--fake-initial']
    smartdb_opts = ['--database=smart_manager', 'smart_manager']

    # Migrate Content types before individual apps
    logger.debug('migrate (--fake-initial) contenttypes')
    run_command(
        fake_initial_migration_cmd + ['--database=default', 'contenttypes'])

    for app in ('storageadmin', 'smart_manager'):
        db = 'default'
        if app == 'smart_manager':
            db = app
        o, e, rc = run_command([DJANGO, 'migrate', '--list',
                                '--database=%s' % db, app])
        initial_faked = False
        for l in o:
            if l.strip() == '[X] 0001_initial':
                initial_faked = True
                break
        if not initial_faked:
            db_arg = '--database=%s' % db
            logger.debug('migrate (--fake) db=({}) app=({}) 0001_initial'
                         .format(db, app))
            run_command(fake_migration_cmd + [db_arg, app, '0001_initial'])

    run_command(migration_cmd + ['auth'])
    run_command(migration_cmd + ['storageadmin'])
    run_command(migration_cmd + smartdb_opts)
    run_command(migration_cmd + ['django_ztask'])
    logging.info('Done')
    logging.info('Running prepdb...')
    run_command([PREP_DB, ])
    logging.info('Done')

    logging.info('stopping firewalld...')
    run_command([SYSCTL, 'stop', 'firewalld'])
    run_command([SYSCTL, 'disable', 'firewalld'])
    logging.info('firewalld stopped and disabled')
    update_nginx(logging)

    shutil.copyfile('/etc/issue', '/etc/issue.rockstor')
    init_update_issue(logging)

    enable_rockstor_service(logging)
    enable_bootstrap_service(logging)


if __name__ == '__main__':
    main()
