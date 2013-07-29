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
from storageadmin.models import User
from system.users import (get_users, useradd, usermod, userdel, get_epasswd)

def register_services():
    service_list = ('nfs', 'samba', 'sftp', 'ldap', 'ad', 'iscsi',)
    for s in service_list:
        if (not Service.objects.filter(name=s).exists()):
            s_o = Service(name=s, registered=True)
            s_o.save()

def create_admin_users():
    #if (not User.objects.filter(username='rocky').exists()):
    #    User.objects.create_user('rocky', 'rocky@rockstor.com', 'iltwas')
    #if (not User.objects.filter(username='admin').exists()):
    #    User.objects.create_user('admin', 'admin@rockstor.com', 'admin')

    defaultUsers = [('admin','admin','admin'),('rocky','iltwas','admin')]
    for u in defaultUsers:
        username = u[0]
        password = u[1]
        print "Creating user %s %s" % (username, password)
        utype = u[2]
        admin = False
        # Add user to django admin users if utype is admin
        # and the admin user does not already exist
        if (utype == 'admin'):
            admin = True
            if (not DjangoUser.objects.filter(username=username).exists()):
                auser = DjangoUser.objects.create_user(username, None, 
                        password)
        
        max_uid = settings.START_UID
        shell = settings.USER_SHELL
        try:
            max_uid = User.objects.all().order_by('-uid')[0].uid
        except:
            pass
        uid = max_uid + 1
        # Add the user to unix users if it doesnt already exist
        if (get_users(uname=username) == {}):
            useradd(username, uid, shell)
            usermod(username, password)
        
        epw = get_epasswd(username)
        # Add the user to rockstor users if it doesnt already exist
        if (not User.objects.filter(name=username).exists()):
            suser = User(name=username, password=epw, uid=uid,
                    gid=uid, admin=admin)
            suser.save()

def main():
    create_admin_users()
    register_services()

