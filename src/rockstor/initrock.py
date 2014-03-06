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

SYSCTL = '/usr/bin/systemctl'

def main():
    run_command([SYSCTL, 'enable', 'postgresql'])
    shutil.rmtree('/var/lib/pgsql/data')
    run_command(['/usr/bin/postgresql-setup', 'initdb'])
    run_command(['cp', '-f', '/opt/rockstor/conf/pg_hba.conf',
                 '/var/lib/pgsql/data/'])
    run_command([SYSCTL, 'restart', 'postgresql'])
    run_command([SYSCTL, 'status', 'postgresql'])
    run_command(['su', '-', 'postgres', '-c', '/usr/bin/createdb smartdb'])
    run_command(['su', '-', 'postgres', '-c', '/usr/bin/createdb storageadmin'])
    run_command(['su', '-', 'postgres', '-c', '/usr/bin/createdb backup'])
    run_command(['sudo', '-u', 'postgres', 'psql', '-c',
                 "CREATE ROLE rocky WITH SUPERUSER LOGIN PASSWORD 'rocky'"])
    run_command(['sudo', '-u', 'postgres', 'psql', 'storageadmin', '-f',
                 '/opt/rockstor/conf/storageadmin.sql.in'])
    run_command(['sudo', '-u', 'postgres', 'psql', 'smartdb', '-f',
                 '/opt/rockstor/conf/smartdb.sql.in'])
    run_command(['sudo', '-u', 'postgres', 'psql', 'backup', '-f',
                 '/opt/rockstor/conf/backup.sql.in'])
    run_command(['sudo', '-u', 'postgres', 'psql', 'storageadmin', '-c', "select setval('south_migrationhistory_id_seq', (select max(id) from south_migrationhistory))"])
    run_command(['sudo', '-u', 'postgres', 'psql', 'smartdb', '-c', "select setval('south_migrationhistory_id_seq', (select max(id) from south_migrationhistory))"])
    run_command(['sudo', '-u', 'postgres', 'psql', 'backup', '-c', "select setval('south_migrationhistory_id_seq', (select max(id) from south_migrationhistory))"])
    shutil.copy('/opt/rockstor/conf/rockstor.service', '/etc/systemd/system/')
    run_command([SYSCTL, 'enable', 'rockstor'])
    run_command([SYSCTL, 'start', 'rockstor'])
    run_command([SYSCTL, 'stop', 'firewalld'])
    run_command([SYSCTL, 'disable', 'firewalld'])
    print('All set. You can use the web-ui now and start using Rockstor!')

if __name__ == '__main__':
    main()
