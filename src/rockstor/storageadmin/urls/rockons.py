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
    RockOnView,
    RockOnIdView,
    RockOnVolumeView,
    RockOnPortView,
    RockOnCustomConfigView,
    RockOnEnvironmentView,
    RockOnDeviceView,
    RockOnContainerView,
    RockOnLabelView,
)

urlpatterns = patterns(
    "",
    url(r"^$", RockOnView.as_view(),),
    url(r"^/volumes/(?P<rid>\d+)$", RockOnVolumeView.as_view(),),
    url(r"^/docker/containers/(?P<rid>\d+)$", RockOnContainerView.as_view(),),
    url(r"^/ports/(?P<rid>\d+)$", RockOnPortView.as_view(),),
    url(r"^/customconfig/(?P<rid>\d+)$", RockOnCustomConfigView.as_view(),),
    url(r"^/environment/(?P<rid>\d+)$", RockOnEnvironmentView.as_view(),),
    url(r"^/devices/(?P<rid>\d+)$", RockOnDeviceView.as_view(),),
    url(r"^/labels/(?P<rid>\d+)$", RockOnLabelView.as_view(),),
    url(r"^/(?P<command>update)$", RockOnView.as_view(),),
    url(r"^/(?P<rid>\d+)$", RockOnIdView.as_view(),),
    url(
        r"^/(?P<rid>\d+)/(?P<command>install|uninstall|update|start|stop|state_update|status_update)$",  # noqa E501
        RockOnIdView.as_view(),
    ),
)
