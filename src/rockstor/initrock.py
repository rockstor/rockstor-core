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

SYSCTL = '/usr/bin/systemctl'
DJANGO = '/opt/rockstor/bin/django'
STAMP = '/opt/rockstor/.initrock'


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


def main():
    loglevel = logging.INFO
    if (len(sys.argv) > 1 and sys.argv[1] == '-x'):
        loglevel = logging.DEBUG
    logging.basicConfig(format='%(asctime)s: %(message)s', level=loglevel)
    shutil.copyfile('/etc/issue', '/etc/issue.rockstor')
    update_issue()
    if (os.path.isfile(STAMP)):
        return logging.info(
            'initrock ran successfully before, not running it again.'
            ' Running it again can destroy your Rockstor state. If you know '
            'what you are doing, remove /opt/rockstor/.initrock '
            'and run again.')
    logging.info('Please be patient. This script could take a few minutes')
    shutil.copyfile('/opt/rockstor/conf/django-hack',
                    '/opt/rockstor/bin/django')
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
    run_command(['su', '-', 'postgres', '-c', '/usr/bin/createdb backup'])
    logging.debug('backup created')
    logging.info('Done')
    logging.info('Initializing app databases...')
    run_command(['su', '-', 'postgres', '-c', "psql -c \"CREATE ROLE rocky WITH SUPERUSER LOGIN PASSWORD 'rocky'\""])
    logging.debug('rocky ROLE created')
    run_command(['su', '-', 'postgres', '-c', "psql storageadmin -f /opt/rockstor/conf/storageadmin.sql.in"])
    logging.debug('storageadmin app database loaded')
    run_command(['su', '-', 'postgres', '-c', "psql smartdb -f /opt/rockstor/conf/smartdb.sql.in"])
    logging.debug('smartdb app database loaded')
    run_command(['su', '-', 'postgres', '-c', "psql backup -f /opt/rockstor/conf/backup.sql.in"])
    logging.debug('backup app database loaded')
    run_command(['su', '-', 'postgres', '-c', "psql storageadmin -c \"select setval('south_migrationhistory_id_seq', (select max(id) from south_migrationhistory))\""])
    logging.debug('storageadmin migration history copied')
    run_command(['su', '-', 'postgres', '-c', "psql smartdb -c \"select setval('south_migrationhistory_id_seq', (select max(id) from south_migrationhistory))\""])
    logging.debug('smartdb migration history copied')
    run_command(['su', '-', 'postgres', '-c', "psql backup -c \"select setval('south_migrationhistory_id_seq', (select max(id) from south_migrationhistory))\""])
    logging.debug('backup migration history copied')
    logging.info('Done')
    run_command(['cp', '-f', '/opt/rockstor/conf/postgresql.conf',
                 '/var/lib/pgsql/data/'])
    logging.debug('postgresql.conf copied')
    run_command(['cp', '-f', '/opt/rockstor/conf/pg_hba.conf',
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
    run_command([DJANGO, 'migrate', 'smart_manager',
                 '--database=smart_manager', '--noinput'])
    logging.debug('smart manager migrated')
    run_command([DJANGO, 'migrate', 'backup', '--database=backup',
                 '--noinput'])
    logging.debug('backup migrated')
    logging.info('Done')
    logging.info('Running prepdb...')
    run_command(['/opt/rockstor/bin/prep_db', ])
    logging.info('Done')
    shutil.copy('/opt/rockstor/conf/rockstor.service', '/etc/systemd/system/')
    run_command([SYSCTL, 'enable', 'rockstor'])
    run_command([SYSCTL, 'start', 'rockstor'])
    logging.info('Started rockstor service')
    logging.info('Shutting down firewall...')
    run_command([SYSCTL, 'stop', 'firewalld'])
    run_command([SYSCTL, 'disable', 'firewalld'])
    run_command(['touch', STAMP])
    logging.info('Done')
    logging.info('All set. Go to the web-ui now and start using Rockstor!')

if __name__ == '__main__':
    main()
