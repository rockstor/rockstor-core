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
from django.conf import settings
from smart_manager.views import (
    ReplicaTrailListView,
    ReplicaShareListView,
    ReplicaShareDetailView,
    ReceiveTrailListView,
    ReceiveTrailDetailView,
    ReplicaTrailDetailView,
    ReplicaDetailView,
    ReceiverPoolListView,
)

share_regex = settings.SHARE_REGEX

urlpatterns = [
    re_path(r"^(?P<rid>[0-9]+)$", ReplicaDetailView.as_view(), name="replica-view"),
    re_path(
        r"^share/(?P<sname>%s)$" % share_regex,
        ReplicaDetailView.as_view(),
        name="replica-view",
    ),
    re_path(r"^trail$", ReplicaTrailListView.as_view(), name="replica-view"),
    re_path(
        r"^trail/replica/(?P<rid>[0-9]+)",
        ReplicaTrailListView.as_view(),
        name="replica-view",
    ),
    re_path(
        r"^trail/(?P<rtid>[0-9]+)",
        ReplicaTrailDetailView.as_view(),
        name="replica-view",
    ),
    re_path(r"^rshare$", ReplicaShareListView.as_view()),
    re_path(r"^rshare/(?P<rid>[0-9]+)$", ReplicaShareDetailView.as_view()),
    re_path(r"^rshare/(?P<sname>%s)$" % share_regex, ReplicaShareDetailView.as_view()),
    re_path(r"^rtrail$", ReceiveTrailListView.as_view()),
    re_path(r"^rtrail/rshare/(?P<rid>[0-9]+)$", ReceiveTrailListView.as_view()),
    re_path(r"^rtrail/(?P<rtid>[0-9]+)", ReceiveTrailDetailView.as_view()),
    re_path(r"^rpool/(?P<auuid>.*)$", ReceiverPoolListView.as_view()),
]
