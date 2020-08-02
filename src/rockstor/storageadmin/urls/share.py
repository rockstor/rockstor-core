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
from storageadmin.views import (
    ShareListView,
    ShareDetailView,
    ShareACLView,
    SnapshotView,
    ShareCommandView,
)

from django.conf import settings

share_regex = settings.SHARE_REGEX
snap_regex = share_regex
snap_command = "clone|repclone"
share_command = "rollback|clone"

urlpatterns = patterns(
    "",
    url(r"^$", ShareListView.as_view(), name="share-view"),
    url(r"^/(?P<sid>\d+)$", ShareDetailView.as_view(), name="share-view"),
    url(r"^/(?P<sid>\d+)/(?P<command>force)$", ShareDetailView.as_view(),),
    # Individual snapshots don't have detailed representation in the web-ui. So
    # thre is no need for SnapshotDetailView.
    url(r"^/(?P<sid>\d+)/snapshots$", SnapshotView.as_view(), name="snapshot-view"),
    url(
        r"^/(?P<sid>\d+)/snapshots/(?P<snap_name>%s)$" % snap_regex,
        SnapshotView.as_view(),
        name="snapshot-view",
    ),
    url(
        r"^/(?P<sid>\d+)/snapshots/(?P<snap_name>%s)/(?P<command>%s)$"
        % (snap_regex, snap_command),
        SnapshotView.as_view(),
    ),
    url(r"^/(?P<sid>\d+)/acl$", ShareACLView.as_view(), name="acl-view"),
    url(r"^/(?P<sid>\d+)/(?P<command>%s)$" % share_command, ShareCommandView.as_view()),
)
