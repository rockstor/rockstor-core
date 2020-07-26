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

from storageadmin.models import RockOn, DContainer
from storageadmin.serializers import RockOnContainerSerializer
import rest_framework_custom as rfc
from storageadmin.util import handle_exception


class RockOnContainerView(rfc.GenericView):
    serializer_class = RockOnContainerSerializer

    def get_queryset(self, *args, **kwargs):
        try:
            rockon = RockOn.objects.get(id=self.kwargs["rid"])
        except:
            e_msg = "Rock-on ({}) does not exist.".format(self.kwargs["rid"])
            handle_exception(Exception(e_msg), self.request)

        containers = DContainer.objects.filter(rockon=rockon)
        return containers.order_by("id")
