"""
Copyright (c) 2012-2020 RockStor, Inc. <http://rockstor.com>
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
from storageadmin.views import CommandView

valid_commands = (
    "uptime|bootstrap|utcnow|update-check|update|current-version"
    "|shutdown|reboot|kernel|current-user|auto-update-status"
    "|enable-auto-update|disable-auto-update|refresh-disk-state"
    "|refresh-pool-state|refresh-share-state"
    "|refresh-snapshot-state"
)

urlpatterns = patterns(
    "",
    url(r"(?P<command>%s)$" % valid_commands, CommandView.as_view(), name="user-view"),
    url(
        r"(?P<command>shutdown|suspend)/(?P<rtcepoch>\d+)$",
        CommandView.as_view(),
        name="user-view",
    ),
)
