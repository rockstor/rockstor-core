"""
Copyright (c) 2012-2013 RockStor, Inc. <http://rockstor.com>
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

from storageadmin.models import (Appliance, Disk, Group, NetworkInterface,
                                 Pool, Share,)
from storageadmin.serializers import (ApplianceSerializer, DiskInfoSerializer,
                                      GroupSerializer, NetworkInterfaceSerializer,
                                      PoolInfoSerializer, ShareSerializer)
import rest_framework_custom as rfc
from rest_framework.response import Response


class ApplianceDetailView(rfc.GenericView):
    serializer_class = ApplianceSerializer

    def get(self, *args, **kwargs):
        if 'ip' in self.kwargs or 'id' in self.kwargs:
            try:
                if 'ip' in self.kwargs:
                    data = Appliance.objects.get(ip=self.kwargs['ip'])
                else:
                    data = Appliance.objects.get(id=self.kwargs['id'])
                serialized_data = ApplianceSerializer(data)
                return Response(serialized_data.data)
            except:
                return Response()


class DiskDetailView(rfc.GenericView):
    serializer_class = DiskInfoSerializer

    def get(self, *args, **kwargs):
        if 'dname' in self.kwargs:
            try:
                data = Disk.objects.get(name=self.kwargs['dname'])
                serialized_data = DiskInfoSerializer(data)
                return Response(serialized_data.data)
            except:
                return Response()


class GroupDetailView(rfc.GenericView):
    serializer_class = GroupSerializer

    def get(self, *args, **kwargs):
        try:
            data = Group.objects.get(username=self.kwargs['groupname'])
            serialized_data = GroupSerializer(data)
            return Response(serialized_data.data)
        except:
            # Render no response if no matches
            return Response()


class NetworkDetailView(rfc.GenericView):
    serializer_class = NetworkInterfaceSerializer

    def get(self, *args, **kwargs):
        try:
            data = NetworkInterface.objects.get(name=self.kwargs['iname'])
            serialized_data = NetworkInterfaceSerializer(data)
            return Response(serialized_data.data)
        except:
            return Response()


class PoolDetailView(rfc.GenericView):
    serializer_class = PoolInfoSerializer

    def get(self, *args, **kwargs):
        try:
            data = Pool.objects.get(name=self.kwargs['pname'])
            serialized_data = PoolInfoSerializer(data)
            return Response(serialized_data.data)
        except:
            return Response()


class DetailShareView(rfc.GenericView):
    serializer_class = ShareSerializer

    def get(self, *args, **kwargs):
            try:
                data = Share.objects.get(name=self.kwargs['sname'])
                serialized_data = ShareSerializer(data)
                return Response(serialized_data.data)
            except:
                return []
