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

from smart_manager.models import Service
from django.conf import settings
from django.contrib.auth.models import User as DjangoUser
from storageadmin.models import User, Setup, Plugin
from system.users import (get_users, useradd, usermod, userdel, get_epasswd)
import datetime

def register_services():
    services = {'NFS': 'nfs',
                'Samba': 'smb',
                'NIS': 'nis',
                'NTP': 'ntpd',
                'AD': 'winbind',
                'LDAP': 'ldap',
                'SFTP': 'sftp',
                'Replication': 'replication',}

    for s in services.keys():
        if (not Service.objects.filter(display_name=s).exists()):
            s_o = Service(display_name=s, name=services[s])
            s_o.save()

def create_setup():
    setup = Setup.objects.all()
    if len(setup) == 0:
        print "Creating setup"
        s = Setup()
        s.save()

def initialize_plugins():
    plugins = Plugin.objects.all()
    if (not Plugin.objects.filter(name='backup').exists()):
        backup = Plugin(
                name='backup',
                display_name='Backup',
                description='Backup Server functionality',
                css_file_name = 'backup',
                js_file_name = 'backup')
        backup.save()

def main():
    create_setup()
    register_services()
    initialize_plugins()

