"""
Copyright (c) 2012-2014 RockStor, Inc. <http://rockstor.com>
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

import rest_framework_custom as rfc
from storageadmin.serializers import DockerContainerSerializer
from system.docker import container_list
from storageadmin.models import DockerContainer


class DockerContainerView(rfc.GenericView):
    serializer_class = DockerContainerSerializer

    def get_queryset(self, *args, **kwargs):
        containers = []
        for con in container_list():
            cc = DockerContainer(container_id=con.container_id,
                                 image=con.image, command=con.command,
                                 created=con.created, status=con.status,
                                 ports=con.ports, name=con.name)
            containers.append(cc)
        return containers

    def post(self, request):
        pass

    def put(self, request):
        pass

    def delete(self, request):
        pass
