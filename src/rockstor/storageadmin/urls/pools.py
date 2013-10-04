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
from storageadmin.views import (PoolView, PoolScrubView)

pool_regex = r'[A-Za-z]+[A-Za-z0-9_]*'

urlpatterns = patterns(
    '',
    url(r'^$', PoolView.as_view(), name='pool-view'),
    url(r'^/(?P<pname>%s)$' % pool_regex, PoolView.as_view(),
        name='pool-view'),
    url(r'^/(?P<pname>%s)/scrub$' % pool_regex, PoolScrubView.as_view(),
        name='pool-scrub-view'),
    url(r'^/(?P<pname>%s)/scrub/(?P<command>.*)$' % pool_regex,
        PoolScrubView.as_view(), name='pool-scrub-view'),
    url(r'^/(?P<pname>%s)/(?P<command>.*)$' % pool_regex,
        PoolView.as_view(), name='pool-view'),
)
