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

from operator import attrgetter
from smart_manager.models import DiskStat
from storageadmin.models import Disk
from smart_manager.serializers import DiskStatSerializer
from generic_sprobe import GenericSProbeView


class DiskStatView(GenericSProbeView):

    serializer_class = DiskStatSerializer
    model_obj = DiskStat

    def _sorted_results(self, sort_col, reverse):
        qs = []
        for d in Disk.objects.all():
            qs.append(self.model_obj.objects.filter(name=d.name).order_by("-ts")[0])
        return sorted(qs, key=attrgetter(sort_col), reverse=reverse)
