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

from smart_manager.taplib.probe_config import TapConfig, TAP_MAP
import rest_framework_custom as rfc
from smart_manager.serializers import SProbeConfigSerializer


class SProbeView(rfc.GenericView):
    serializer_class = SProbeConfigSerializer

    def get_queryset(self):
        config_list = []
        self.paginate_by = 0
        for pid in TAP_MAP.keys():
            config_list.append(
                TapConfig(
                    uuid=pid,
                    location=TAP_MAP[pid]["location"],
                    sdetail=TAP_MAP[pid]["sdetail"],
                )
            )
        return config_list
