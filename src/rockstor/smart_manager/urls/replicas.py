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
from smart_manager.views import (ReplicaView, ReplicaTrailView,
                                 ReplicaShareView, ReceiveTrailView)

share_regex = r'[A-Za-z]+[A-Za-z0-9_\-.]*'

urlpatterns = patterns('',
    url(r'^$', ReplicaView.as_view(), name='replica-view'),
    url(r'^(?P<rid>[0-9]+)$', ReplicaView.as_view(), name='replica-view'),
    url(r'^share/(?P<sname>%s)$' % share_regex, ReplicaView.as_view(),
        name='replica-view'),

    url(r'^trail$', ReplicaTrailView.as_view(), name='replica-view'),
    url(r'^trail/replica/(?P<rid>[0-9]+)', ReplicaTrailView.as_view(), name='replica-view'),
    url(r'^trail/(?P<rtid>[0-9]+)', ReplicaTrailView.as_view(),
        name='replica-view'),

    url(r'^rshare$', ReplicaShareView.as_view()),
    url(r'^rshare/(?P<sname>%s)$' % share_regex, ReplicaShareView.as_view()),
    url(r'^rshare/(?P<rid>[0-9]+)', ReplicaShareView.as_view()),
    url(r'^rtrail$', ReceiveTrailView.as_view()),
    url(r'^rtrail/rshare/(?P<rid>[0-9]+)', ReceiveTrailView.as_view()),
    url(r'^rtrail/(?P<rtid>[0-9]+)', ReceiveTrailView.as_view()),

)
