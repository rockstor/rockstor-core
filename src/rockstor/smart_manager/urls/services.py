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

from django.conf.urls.defaults import patterns, url
from smart_manager.views import (BaseServiceView, NISServiceView,
                                 SambaServiceView, NFSServiceView,
                                 NTPServiceView)

command_regex = ('config|start|stop')

urlpatterns = patterns('',
    # Services
    url(r'^$', BaseServiceView.as_view(), name='service-view'),
    url(r'^nis$', NISServiceView.as_view(), name='nis-view'),
    url(r'^nis/(?P<command>%s)$' % command_regex, NISServiceView.as_view(),
        name='nis-view'),
    url(r'^smb$', SambaServiceView.as_view(), name='samba-view'),
    url(r'^smb/(?P<command>%s)$' % command_regex, SambaServiceView.as_view(),
        name='samba-view'),
    url(r'^nfs$', NFSServiceView.as_view(), name='nfs-view'),
    url(r'^nfs/(?P<command>%s)$' % command_regex, NFSServiceView.as_view(),
        name='nfs-view'),
    url(r'^ntpd$', NTPServiceView.as_view(), name='ntp-view'),
    url(r'^ntpd/(?P<command>%s)$' % command_regex, NTPServiceView.as_view(),
        name='ntp-view'),
)
