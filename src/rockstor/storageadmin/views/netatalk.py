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
from storageadmin.models import (NetatalkShare, Disk)
from storageadmin.util import handle_exception
from storageadmin.serializers import NetatalkShareSerializer
from storageadmin.exceptions import RockStorAPIException
from fs.btrfs import (mount_share, is_share_mounted)
from system.services import (restart_netatalk, refresh_afp_config)
import rest_framework_custom as rfc
from share_helpers import validate_share


import logging
logger = logging.getLogger(__name__)


class NetatalkView(rfc.GenericView):
    serializer_class = NetatalkShareSerializer
    def_description = 'on Rockstor'

    def get_queryset(self, *args, **kwargs):
        if ('id' in kwargs):
            self.paginate_by = 0
            try:
                return NetatalkShare.objects.get(id=kwargs['id'])
            except:
                return []
        return NetatalkShare.objects.all()

    @transaction.commit_on_success
    def post(self, request):
        if ('shares' not in request.DATA):
            e_msg = ('Must provide share names')
            handle_exception(Exception(e_msg), request)

        shares = [validate_share(s, request) for s in request.DATA['share']]
        description = request.DATA.get('description', '')
        if (description == ''):
            description = self.def_description

        time_machine = request.DATA.get('time_machine', 'yes')
        if (time_machine != 'yes' and time_machine != 'no'):
            e_msg = ('time_machine must be yes or now. not %s' %
                     time_machine)
            handle_exception(Exception(e_msg), request)

        for share in shares:
            if (NetatalkShare.objects.filter(share=share).exists()):
                e_msg = ('Share(%s) is already exported via AFP' % share.name)
                handle_exception(Exception(e_msg), request)

        try:
            for share in shares:
                cur_description = '%s %s' % (share.name, description)
                if (len(shares) == 1 and description != self.def_description):
                    cur_description = description
                afpo = NetatalkShare(share=share, description=cur_description,
                                     time_machine=time_machine)
                afpo.save()

                mnt_pt = ('%s%s' % (settings.MNT_PT, share.name))
                if (not is_share_mounted(share.name)):
                    pool_device = Disk.objects.filter(pool=share.pool)[0].name
                    mount_share(share.subvol_name, pool_device, mnt_pt)
            refresh_afp_config(list(NetatalkShare.objects.all()))
            restart_netatalk()
            return Response()
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)

    @transaction.commit_on_success
    def delete(self, request, afp_id):
        try:
            afpo = NetatalkShare.objects.get(id=afp_id)
            afpo.delete()
        except:
            e_msg = ('AFP config for the id(%s) does not exist' % id)
            handle_exception(Exception(e_msg), request)

        try:
            refresh_afp_config(list(NetatalkShare.objects.all()))
            restart_netatalk()
            return Response()
        except Exception, e:
            logger.exception(e)
            e_msg = ('System error occured while restarting Netatalk server')
            handle_exception(Exception(e_msg), request)
