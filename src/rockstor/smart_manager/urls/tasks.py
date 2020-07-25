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
from smart_manager.views import (
    TaskSchedulerListView,
    TaskLogView,
    TaskTypeView,
    TaskSchedulerDetailView,
)

urlpatterns = patterns(
    "",
    url(r"^$", TaskSchedulerListView.as_view(),),
    url(r"^(?P<tdid>\d+)$", TaskSchedulerDetailView.as_view(),),
    url(r"^log$", TaskLogView.as_view(),),
    url(r"^log/(?P<command>prune)$", TaskLogView.as_view(),),
    url(r"^log/taskdef/(?P<tdid>\d+)", TaskLogView.as_view(),),
    url(r"^log/(?P<tid>\d+)", TaskLogView.as_view(),),
    url(r"^types$", TaskTypeView.as_view(),),
)
