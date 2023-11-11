"""
Copyright (c) 2012-2023 RockStor, Inc. <https://rockstor.com>
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
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

from django.urls import re_path
from smart_manager.views import (
    ActiveDirectoryServiceView,
    BootstrapServiceView,
    DataCollectorServiceView,
    DockerServiceView,
    LdapServiceView,
    NFSServiceView,
    NISServiceView,
    NTPServiceView,
    NUTServiceView,
    ReplicationServiceView,
    RockstorServiceView,
    SFTPServiceView,
    SMARTDServiceView,
    SNMPServiceView,
    SambaServiceView,
    ShellInABoxServiceView,
    ServiceMonitorView,
    TaskSchedulerServiceView,
    ZTaskdServiceView,
    TailscaledServiceView,
)

command_regex = "config|start|stop"
action_regex = "login|logout"

urlpatterns = [
    # Services
    re_path(r"^nis$", NISServiceView.as_view()),
    re_path(r"^nis/(?P<command>%s)$" % command_regex, NISServiceView.as_view()),
    re_path(r"^smb$", SambaServiceView.as_view()),
    re_path(r"^smb/(?P<command>%s)$" % command_regex, SambaServiceView.as_view()),
    re_path(r"^nfs$", NFSServiceView.as_view()),
    re_path(r"^nfs/(?P<command>%s)$" % command_regex, NFSServiceView.as_view()),
    re_path(r"^ntpd$", NTPServiceView.as_view()),
    re_path(r"^ntpd/(?P<command>%s)$" % command_regex, NTPServiceView.as_view()),
    re_path(r"^active-directory$", ActiveDirectoryServiceView.as_view()),
    re_path(
        r"^active-directory/(?P<command>%s)$" % command_regex,
        ActiveDirectoryServiceView.as_view(),
    ),
    re_path(r"^ldap$", LdapServiceView.as_view()),
    re_path(r"^ldap/(?P<command>%s)$" % command_regex, LdapServiceView.as_view()),
    re_path(r"^sftp$", SFTPServiceView.as_view()),
    re_path(r"^sftp/(?P<command>%s)$" % command_regex, SFTPServiceView.as_view()),
    re_path(r"^replication$", ReplicationServiceView.as_view()),
    re_path(
        r"^replication/(?P<command>%s)$" % command_regex,
        ReplicationServiceView.as_view(),
    ),
    re_path(r"^task-scheduler$", TaskSchedulerServiceView.as_view()),
    re_path(
        r"^task-scheduler/(?P<command>%s)$" % command_regex,
        TaskSchedulerServiceView.as_view(),
    ),
    re_path(r"^data-collector$", DataCollectorServiceView.as_view()),
    re_path(
        r"^data-collector/(?P<command>%s)$" % command_regex,
        DataCollectorServiceView.as_view(),
    ),
    re_path(r"^service-monitor$", ServiceMonitorView.as_view()),
    re_path(
        r"^service-monitor/(?P<command>%s)$" % command_regex,
        ServiceMonitorView.as_view(),
    ),
    re_path(r"^snmpd$", SNMPServiceView.as_view()),
    re_path(r"^snmpd/(?P<command>%s)$" % command_regex, SNMPServiceView.as_view()),
    re_path(r"^docker$", DockerServiceView.as_view()),
    re_path(r"^docker/(?P<command>%s)$" % command_regex, DockerServiceView.as_view()),
    re_path(r"^smartd$", SMARTDServiceView.as_view()),
    re_path(r"^smartd/(?P<command>%s)$" % command_regex, SMARTDServiceView.as_view()),
    re_path(r"^nut$", NUTServiceView.as_view()),
    re_path(r"^nut/(?P<command>%s)$" % command_regex, NUTServiceView.as_view()),
    re_path(r"^ztask-daemon$", ZTaskdServiceView.as_view()),
    re_path(r"^ztask-daemon/(?P<command>%s)$" % command_regex, ZTaskdServiceView.as_view()),
    re_path(r"^rockstor-bootstrap$", BootstrapServiceView.as_view()),
    re_path(
        r"^rockstor-bootstrap/(?P<command>%s)$" % command_regex,
        BootstrapServiceView.as_view(),
    ),
    re_path(r"^shellinaboxd$", ShellInABoxServiceView.as_view()),
    re_path(
        r"^shellinaboxd/(?P<command>%s)$" % command_regex,
        ShellInABoxServiceView.as_view(),
    ),
    re_path(r"^rockstor$", RockstorServiceView.as_view()),
    re_path(r"^rockstor/(?P<command>%s)$" % command_regex, RockstorServiceView.as_view()),
    re_path(r"^tailscaled$", TailscaledServiceView.as_view()),
    re_path(
        r"^tailscaled/(?P<command>%s)$" % command_regex, TailscaledServiceView.as_view()
    ),
    re_path(
        r"^tailscaled/(?P<command>%s)/(?P<action>%s)$" % (command_regex, action_regex),
        TailscaledServiceView.as_view(),
    ),
]
