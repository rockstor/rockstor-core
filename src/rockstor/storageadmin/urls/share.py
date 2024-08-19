"""
Copyright (joint work) 2024 The Rockstor Project <https://rockstor.com>

Rockstor is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

Rockstor is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

from django.urls import re_path
from storageadmin.views import (
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

urlpatterns = [
    re_path(r"^(?P<sid>\d+)$", ShareDetailView.as_view(), name="share-view"),
    re_path(r"^(?P<sid>\d+)/(?P<command>force)$", ShareDetailView.as_view(),),
    # Individual snapshots don't have detailed representation in the web-ui. So
    # thre is no need for SnapshotDetailView.
    re_path(r"^(?P<sid>\d+)/snapshots$", SnapshotView.as_view(), name="snapshot-view"),
    re_path(
        r"^(?P<sid>\d+)/snapshots/(?P<snap_name>%s)$" % snap_regex,
        SnapshotView.as_view(),
        name="snapshot-view",
    ),
    re_path(
        r"^(?P<sid>\d+)/snapshots/(?P<snap_name>%s)/(?P<command>%s)$"
        % (snap_regex, snap_command),
        SnapshotView.as_view(),
    ),
    re_path(r"^(?P<sid>\d+)/acl$", ShareACLView.as_view(), name="acl-view"),
    re_path(r"^(?P<sid>\d+)/(?P<command>%s)$" % share_command, ShareCommandView.as_view()),
]
