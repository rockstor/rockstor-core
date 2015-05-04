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

from django.conf.urls import patterns, url
from smart_manager.views import (NISServiceView,
                                 SambaServiceView, NFSServiceView,
                                 NTPServiceView, WinbindServiceView,
                                 LdapServiceView, SFTPServiceView,
                                 ReplicationServiceView,
                                 TaskSchedulerServiceView,
                                 DataCollectorServiceView, ServiceMonitorView,
                                 AFPServiceView, SNMPServiceView,
                                 DockerServiceView)
from smart_manager.views.base_list_service import BaseServiceListView
command_regex = ('config|start|stop')

urlpatterns = patterns('',
    # Services
    url(r'^$', BaseServiceListView.as_view()),
    url(r'^netatalk$', AFPServiceView.as_view()),
    url(r'^netatalk/(?P<command>%s)$' % command_regex,
        AFPServiceView.as_view()),
    url(r'^nis$', NISServiceView.as_view()),
    url(r'^nis/(?P<command>%s)$' % command_regex, NISServiceView.as_view()),
    url(r'^smb$', SambaServiceView.as_view()),
    url(r'^smb/(?P<command>%s)$' % command_regex, SambaServiceView.as_view()),
    url(r'^nfs$', NFSServiceView.as_view()),
    url(r'^nfs/(?P<command>%s)$' % command_regex, NFSServiceView.as_view()),
    url(r'^ntpd$', NTPServiceView.as_view()),
    url(r'^ntpd/(?P<command>%s)$' % command_regex, NTPServiceView.as_view()),
    url(r'^winbind$', WinbindServiceView.as_view()),
    url(r'^winbind/(?P<command>%s)$' % command_regex,
        WinbindServiceView.as_view()),
    url(r'^ldap$', LdapServiceView.as_view()),
    url(r'^ldap/(?P<command>%s)$' % command_regex, LdapServiceView.as_view()),
    url(r'^sftp$', SFTPServiceView.as_view()),
    url(r'^sftp/(?P<command>%s)$' % command_regex, SFTPServiceView.as_view()),
    url(r'^replication$', ReplicationServiceView.as_view()),
    url(r'^replication/(?P<command>%s)$' % command_regex,
        ReplicationServiceView.as_view()),
    url(r'^task-scheduler$', TaskSchedulerServiceView.as_view()),
    url(r'^task-scheduler/(?P<command>%s)$' % command_regex,
        TaskSchedulerServiceView.as_view()),
    url(r'^data-collector$', DataCollectorServiceView.as_view()),
    url(r'^data-collector/(?P<command>%s)$' % command_regex,
        DataCollectorServiceView.as_view()),
    url(r'^service-monitor$', ServiceMonitorView.as_view()),
    url(r'^service-monitor/(?P<command>%s)$' % command_regex,
        ServiceMonitorView.as_view()),
    url(r'^snmpd$', SNMPServiceView.as_view()),
    url(r'^snmpd/(?P<command>%s)$' % command_regex, SNMPServiceView.as_view()),
    url(r'^docker$', DockerServiceView.as_view()),
    url(r'^docker/(?P<command>%s)$' % command_regex,
        DockerServiceView.as_view()),
)
