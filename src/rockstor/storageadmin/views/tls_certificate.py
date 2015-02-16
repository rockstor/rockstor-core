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

from rest_framework.response import Response
from django.db import transaction
from django.conf import settings
from storageadmin.models import (SambaShare, TLSCertificate, User, SambaCustomConfig)
from storageadmin.serializers import TLSCertificateSerializer
from storageadmin.util import handle_exception
import rest_framework_custom as rfc
from share_helpers import validate_share
from system.samba import (refresh_smb_config, status, restart_samba)
from fs.btrfs import (mount_share, is_share_mounted)

import logging
logger = logging.getLogger(__name__)


class TLSCertificateView(rfc.GenericView):
    serializer_class = TLSCertificateSerializer

    def get_queryset(self, *args, **kwargs):
        return []


    @transaction.commit_on_success
    def post(self, request):
            return Response()
