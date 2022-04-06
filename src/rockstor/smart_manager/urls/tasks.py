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

#from django.conf.urls import patterns, urls
from django.urls import include, re_path
from smart_manager.views import (
    TaskLogView,
    TaskTypeView,
    TaskSchedulerDetailView,
)

urlpatterns = [
    re_path(r"^$", TaskSchedulerListView.as_view(),),
    re_path(r"^(?P<tdid>\d+)$", TaskSchedulerDetailView.as_view(),),
    re_path(r"^log$", TaskLogView.as_view(),),
    re_path(r"^log/(?P<command>prune)$", TaskLogView.as_view(),),
    re_path(r"^log/taskdef/(?P<tdid>\d+)", TaskLogView.as_view(),),
    re_path(r"^log/(?P<tid>\d+)", TaskLogView.as_view(),),
    re_path(r"^types$", TaskTypeView.as_view(),),
]
