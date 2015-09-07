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
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from system.osi import run_command
import logging
import sys
import re
import time
from tempfile import mkstemp
import hashlib
from django.conf import settings


SYSCTL = '/usr/bin/systemctl'
BASE_DIR = settings.ROOT_DIR
BASE_BIN = '%s/bin' % BASE_DIR
DJANGO = '%s/django' % BASE_BIN
STAMP = '%s/.initrock' % BASE_DIR
FLASH_OPTIMIZE = '%s/flash-optimize' % BASE_BIN
PREP_DB = '%s/prep_db' % BASE_BIN
QGROUP_CLEAN = '%s/qgroup-clean' % BASE_BIN
QGROUP_MAXOUT_LIMIT = '%s/qgroup-maxout-limit' % BASE_BIN
SUPERCTL = '%s/supervisorctl' % BASE_BIN
OPENSSL = '/usr/bin/openssl'
GRUBBY = '/usr/sbin/grubby'


def update_issue():
    default_if = None
    ipaddr = None
    o, e, c = run_command(['/usr/sbin/route'])
    for i in o:
        if (re.match('default', i) is not None):
            default_if = i.split()[-1]
    if (default_if is not None):
        o2, e, c = run_command(['/usr/sbin/ifconfig', default_if])
        for i2 in o2:
            if (re.match('inet ', i2.strip()) is not None):
                ipaddr = i2.split()[1]
    with open('/etc/issue', 'w') as ifo:
        if (ipaddr is None):
            ifo.write('The system does not have an ip address.\n\n')
            ifo.write('Rockstor cannot be configured using the web-ui '
                      'without an ip address.\n\n')
            ifo.write('Login as root and configure your network to proceed '
                      'further.\n')
        else:
            ifo.write('\nRockstor is successfully installed.\n\n')
            ifo.write('You can access the web-ui by pointing your browser to '
                      'https://%s\n\n' % ipaddr)


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
        logger.error('Exception while listing the default kernel')
        return logger.exception(e)

    try:
        run_command([GRUBBY, '--set-default=%s' % supported_kernel_path])
        return logger.info('Default kernel set to %s' % supported_kernel_path)
    except Exception, e:
        logger.error('Exception while setting kernel(%s) as default' % version)
        return logger.exception(e)

def update_tz(logging):
    #update timezon variable in settings.py
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
                #if header is found,
                found = True
                logging.info('sshd_config already has the updates.'
                             ' Leaving it unchanged.')
                break
        if (not found):
            sfo.write('%s\n' % settings.SSHD_HEADER)
            sfo.write('AllowUsers root\n')
            logging.info('updated sshd_config')
            run_command([SYSCTL, 'restart', 'sshd'])

def md5sum(fpath):
    #return the md5sum of the given file
    if (not os.path.isfile(fpath)):
        return None
    md5 = hashlib.md5()
    with open(fpath) as tfo:
        for l in tfo.readlines():
            md5.update(l)
    return md5.hexdigest()

def enable_rockstor_service(logging):
    rs_dest = '/etc/systemd/system/rockstor.service'
    rs_src = '%s/conf/rockstor.service' % BASE_DIR
    sum1 = md5sum(rs_dest)
    sum2 = md5sum(rs_src)
    if (sum1 != sum2):
        logging.info('updating rockstor systemd service')
        shutil.copy(rs_src, rs_dest)
        run_command([SYSCTL, 'enable', 'rockstor'])
        run_command([SYSCTL, 'start', 'rockstor'])
        logging.info('Started rockstor service')

def main():
    loglevel = logging.INFO
    if (len(sys.argv) > 1 and sys.argv[1] == '-x'):
        loglevel = logging.DEBUG
    logging.basicConfig(format='%(asctime)s: %(message)s', level=loglevel)
    set_def_kernel(logging)
    shutil.copyfile('/etc/issue', '/etc/issue.rockstor')
    for i in range(30):
        try:
            update_issue()
            break
        except Exception, e:
            logging.info('exception occured while running update_issue. '
                         'Perhaps rc.local ran before it should have. '
                         'Trying again after 2 seconds')
            if (i > 28):
                logging.info('Waited too long and tried too many times. '
                             'Quiting.')
                raise e
            time.sleep(2)
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

    with open('/etc/rc.d/rc.local', 'a+') as lfo:
        found = False
        initrock_loc = '%s/initrock' % BASE_BIN
        for l in lfo.readlines():
            if (re.match(initrock_loc, l) is not None):
                found = True
        if (not found):
            lfo.write('#rockstor script. dont remove\n')
            lfo.write('%s -x\n' % initrock_loc)
    run_command(['/usr/bin/chmod', 'a+x', '/etc/rc.d/rc.local'])
    logging.info('Checking for flash and Running flash optimizations if appropriate.')
    run_command([FLASH_OPTIMIZE, '-x'])
    tz_updated = False
    try:
        logging.info('Updating the timezone from the system')
        tz_updated = update_tz(logging)
    except Exception, e:
        logging.error('Exception while updating timezone: %s' % e.__str__())

    try:
        logging.info('Updating sshd_config')
        bootstrap_sshd_config(logging)
    except Exception, e:
        logging.error('Exception while updating sshd_config: %s' % e.__str__())

    if (os.path.isfile(STAMP)):
        logging.info('Running prepdb...')
        run_command([PREP_DB, ])
        try:
            logging.info('Running qgroup cleanup. %s' % QGROUP_CLEAN)
            run_command([QGROUP_CLEAN])
        except Exception, e:
            logging.error('Exception while running %s: %s' % (QGROUP_CLEAN, e.__str__()))

        try:
            logging.info('Running qgroup limit maxout. %s' % QGROUP_MAXOUT_LIMIT)
            run_command([QGROUP_MAXOUT_LIMIT])
        except Exception, e:
            logging.error('Exception while running %s: %s' % (QGROUP_MAXOUT_LIMIT, e.__str__()))

        enable_rockstor_service(logging)
        if (tz_updated):
            run_command([SYSCTL, 'restart', 'rockstor'])
        return logging.info(
            'initrock ran successfully before, so not running it again.'
            ' Running it again can destroy your Rockstor state. If you know '
            'what you are doing, remove %s/.initrock '
            'and run again.' % BASE_DIR)
    logging.info('Please be patient. This script could take a few minutes')
    shutil.copyfile('%s/conf/django-hack' % BASE_DIR,
                    '%s/django' % BASE_BIN)
    run_command([SYSCTL, 'enable', 'postgresql'])
    logging.debug('Progresql enabled')
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
    run_command(['su', '-', 'postgres', '-c', "psql storageadmin -c \"select setval('south_migrationhistory_id_seq', (select max(id) from south_migrationhistory))\""])
    logging.debug('storageadmin migration history copied')
    run_command(['su', '-', 'postgres', '-c', "psql smartdb -c \"select setval('south_migrationhistory_id_seq', (select max(id) from south_migrationhistory))\""])
    logging.debug('smartdb migration history copied')
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
    run_command([DJANGO, 'migrate', 'oauth2_provider', '--database=default',
                 '--noinput'])
    run_command([DJANGO, 'migrate', 'storageadmin', '--database=default',
                 '--noinput'])
    logging.debug('storageadmin migrated')
    run_command([DJANGO, 'migrate', 'django_ztask', '--database=default',
                 '--noinput'])
    logging.debug('django_ztask migrated')
    run_command([DJANGO, 'migrate', 'smart_manager',
                 '--database=smart_manager', '--noinput'])
    logging.debug('smart manager migrated')
    logging.info('Done')
    logging.info('Running prepdb...')
    run_command([PREP_DB, ])
    logging.info('Done')
    enable_rockstor_service(logging)
    logging.info('Started rockstor service')
    logging.info('Shutting down firewall...')
    run_command([SYSCTL, 'stop', 'firewalld'])
    run_command([SYSCTL, 'disable', 'firewalld'])
    run_command(['touch', STAMP])
    logging.info('Done')
    logging.info('All set. Go to the web-ui now and start using Rockstor!')

if __name__ == '__main__':
    main()
