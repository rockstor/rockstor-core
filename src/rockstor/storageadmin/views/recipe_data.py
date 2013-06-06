from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from rest_framework.permissions import IsAuthenticated
from storageadmin.auth import DigestAuthentication
from django.db import transaction
from storageadmin.models import (Share, Snapshot, Disk, Qgroup, Pool)
from fs.btrfs import (add_share, remove_share, share_id, update_quota,
                      share_usage)
from storageadmin.serializers import ShareSerializer
from storageadmin.util import handle_exception
from storageadmin.exceptions import RockStorAPIException

import logging
logger = logging.getLogger(__name__)

class RecipeDataView(APIView):

    def get(self, request, rname=None):
        try:
            data = [ { x: 1, y: 2}, { x: 2, y: 5} ]

            return Response(data,
                    status = status.HTTP_201_CREATED)

        except Exception, e:
            handle_exception(e, request)
            


