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

from rest_framework.response import Response
from django.db import transaction
from storageadmin.util import handle_exception
from storageadmin.serializers import GroupSerializer
from storageadmin.models import Group
import rest_framework_custom as rfc
from system.users import (groupadd, groupdel)
import grp
from ug_helpers import combined_groups
import logging
import re
from django.conf import settings
logger = logging.getLogger(__name__)


class GroupView(rfc.GenericView):
    serializer_class = GroupSerializer
    exclude_list = ('root', 'bin', 'daemon', 'sys', 'adm', 'tty', 'disk',
                    'lp', 'mem', 'kmem', 'wheel', 'cdrom', 'mail', 'man',
                    'dialout', 'floppy', 'games', 'tape', 'video', 'ftp',
                    'lock', 'audio', 'nobody', 'users', 'utmp', 'utempter',
                    'ssh_keys', 'systemd-journal', 'dbus', 'rpc', 'polkitd',
                    'avahi', 'avahi-autoipd', 'wbpriv', 'rpcuser', 'nfsnobody',
                    'postgres', 'ntp', 'dip', 'stapusr', 'stapsys', 'stapdev',
                    'nginx', 'postdrop', 'postfix', 'sshd', 'chrony',
                    'usbmuxd')

    def get_queryset(self, *args, **kwargs):
        if ('groupname' in kwargs):
            self.paginate_by = 0
            try:
                return Group.objects.get(username=kwargs['groupname'])
            except:
                return []
        return combined_groups()

    @transaction.commit_on_success
    def post(self, request):
        groupname = request.DATA.get('groupname', None)
        gid = request.DATA.get('gid', None)
        if (groupname is None or
            re.match(settings.USERNAME_REGEX, groupname) is None):
            e_msg = ('Groupname is invalid. It must confirm to the regex: %s' %
                     (settings.USERNAME_REGEX))
            handle_exception(Exception(e_msg), request)
        if (len(groupname) > 30):
            e_msg = ('Groupname cannot be more than 30 characters long')
            handle_exception(Exception(e_msg), request)

        for g in combined_groups():
            if (g.groupname == groupname):
                e_msg = ('Group(%s) already exists. Choose a different one' %
                         g.groupname)
                handle_exception(Exception(e_msg), request)
            if (g.gid == gid):
                e_msg = ('GID(%s) already exists. Choose a different one' %
                         gid)
                handle_exception(Exception(e_msg), request)

        groupadd(groupname, gid)
        grp_entries = grp.getgrnam(groupname)
        gid = grp_entries[2]
        group = Group(gid=gid, groupname=groupname, admin=True)
        group.save()

        return Response(GroupSerializer(group).data)

    def put(self, request, groupname):
        e_msg = ('group edit is not supported')
        handle_exception(Exception(e_msg), request)

    @transaction.commit_on_success
    def delete(self, request, groupname):
        if (groupname in self.exclude_list):
            e_msg = ('Delete of restricted group(%s) is not supported.' %
                     groupname)
            handle_exception(Exception(e_msg), request)

        if (Group.objects.filter(groupname=groupname).exists()):
            g = Group.objects.get(groupname=groupname)
            g.delete()
        else:
            found = False
            for g in combined_groups():
                if (g.groupname == groupname):
                    found = True
                    break
            if (found is False):
                e_msg = ('Group(%s) does not exist' % groupname)
                handle_exception(Exception(e_msg), request)

        try:
            groupdel(groupname)
        except Exception, e:
            handle_exception(e, request)

        return Response()
