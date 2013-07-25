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
from smart_manager.views import (SmartManagerView, ServiceView, SProbeView,
                                 MemInfoView, NetStatView,
                                 DiskStatView, NFSDistribView,
                                 NFSDClientDistribView, NFSDShareDistribView,
                                 NFSDShareClientDistribView)


urlpatterns = patterns('',
    # Services
    url(r'^$', ServiceView.as_view(), name='service-view'),
    url(r'^/(?P<sname>[A-Za-z_]+)/$', ServiceView.as_view(),
        name='service-view'),
)
