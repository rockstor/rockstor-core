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
from storageadmin.models import (Share, SambaShare)
from storageadmin.serializers import SambaShareSerializer
from storageadmin.util import handle_exception
from storageadmin.exceptions import RockStorAPIException
from generic_view import GenericView

import logging
logger = logging.getLogger(__name__)

class SambaView(GenericView):
    serializer_class = SambaShareSerializer

    def get_queryset(self, *args, **kwargs):
        try:
            return SambaShare.objects.all()
        except:
            return []

