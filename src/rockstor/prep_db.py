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
from django.contrib.auth.models import User

def register_services():
    service_list = ('nfs', 'samba', 'sftp', 'ldap', 'ad', 'iscsi',)
    for s in service_list:
        if (not Service.objects.filter(name=s).exists()):
            s_o = Service(name=s, registered=True)
            s_o.save()

def create_admin_users():
    if (not User.objects.filter(username='rocky').exists()):
        User.objects.create_user('rocky', 'rocky@rockstor.com', 'iltwas')
    if (not User.objects.filter(username='admin').exists()):
        User.objects.create_user('admin', 'admin@rockstor.com', 'admin')

def main():
    create_admin_users()
    register_services()

