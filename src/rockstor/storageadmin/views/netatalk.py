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

from rest_framework.response import Response
from django.db import transaction
from django.conf import settings
from storageadmin.models import NetatalkShare
from storageadmin.util import handle_exception
from storageadmin.serializers import NetatalkShareSerializer
from storageadmin.exceptions import RockStorAPIException
from fs.btrfs import mount_share
from system.services import (systemctl, refresh_afp_config)
import rest_framework_custom as rfc
from share_helpers import validate_share


import logging
logger = logging.getLogger(__name__)


class NetatalkDetailView(rfc.GenericView):
    def get(self, *args, **kwargs):
        try:
            data = NetatalkShare.objects.get(id=self.kwargs['id'])
            serialized_data = NetatalkShareSerializer(data)
            return Response(serialized_data.data)
        except:
            return Response()

    @transaction.atomic
    def put(self, request, afp_id):
        afpo = self._validate_afp_id(request, afp_id)
        afpo.time_machine = self._validate_input(request)
        afpo.save()
        self._refresh_and_reload(request)
        return Response(NetatalkShareSerializer(afpo).data)

    @transaction.atomic
    def delete(self, request, afp_id):
        afpo = self._validate_afp_id(request, afp_id)
        try:
            afpo.delete()
        except:
            e_msg = 'Failed to delete AFP config for id ({}).'.format(afp_id)
            handle_exception(Exception(e_msg), request)

        self._refresh_and_reload(request)
        return Response()

    @staticmethod
    def _validate_afp_id(request, afp_id):
        try:
            return NetatalkShare.objects.get(id=afp_id)
        except:
            e_msg = 'AFP export for the id ({}) does not exist.'.format(afp_id)
            handle_exception(Exception(e_msg), request)

    @staticmethod
    def _validate_input(request):
        time_machine = request.data.get('time_machine', 'yes')
        if (time_machine != 'yes' and time_machine != 'no'):
            e_msg = ('Time_machine must be yes or no. '
                     'Not ({}).').format(time_machine)
            handle_exception(Exception(e_msg), request)
        return time_machine

    @staticmethod
    def _refresh_and_reload(request):
        try:
            refresh_afp_config(list(NetatalkShare.objects.all()))
            return systemctl('netatalk', 'reload-or-restart')
        except Exception as e:
            e_msg = ('Failed to reload Netatalk server. '
                     'Exception: ({}).').format(e.__str__())
            handle_exception(Exception(e_msg), request)


class NetatalkListView(rfc.GenericView):
    serializer_class = NetatalkShareSerializer
    def_description = 'on Rockstor'

    def get_queryset(self, *args, **kwargs):
        return NetatalkShare.objects.all()

    @transaction.atomic
    def post(self, request):
        if ('shares' not in request.data):
            e_msg = 'Must provide share names.'
            handle_exception(Exception(e_msg), request)

        shares = [validate_share(s, request) for s in request.data['shares']]
        description = request.data.get('description', '')
        if (description == ''):
            description = self.def_description

        time_machine = request.data.get('time_machine', 'yes')
        if (time_machine != 'yes' and time_machine != 'no'):
            e_msg = ('Time_machine must be yes or no. '
                     'Not ({}).').format(time_machine)
            handle_exception(Exception(e_msg), request)

        for share in shares:
            if (NetatalkShare.objects.filter(share=share).exists()):
                e_msg = ('Share ({}) is already exported '
                         'via AFP.').format(share.name)
                handle_exception(Exception(e_msg), request)

        try:
            for share in shares:
                mnt_pt = ('%s%s' % (settings.MNT_PT, share.name))
                cur_description = '%s' % share.name
                #cur_description = '%s %s' % (share.name, description)
                if (len(shares) == 1 and description != self.def_description and share.name == ''):
                    cur_description = description
                afpo = NetatalkShare(share=share, path=mnt_pt,
                                     description=cur_description,
                                     time_machine=time_machine)
                afpo.save()
                if not share.is_mounted:
                    mount_share(share, mnt_pt)
            refresh_afp_config(list(NetatalkShare.objects.all()))
            systemctl('netatalk', 'reload-or-restart')
            return Response()
        except RockStorAPIException:
            raise
        except Exception as e:
            handle_exception(e, request)
