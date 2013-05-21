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
import random

import logging
logger = logging.getLogger(__name__)

class RecipeView(APIView):
    def post(self, request, rname=None):
        try:
            logger.debug('in RecipeView')
            return Response({"recipe_uri": "/api/recipes/nfs/123"})
        except Exception, e:
            handle_exception(e, request)

    def get(self, request, recipe_id=None):
        try:
            if 'status' in request.QUERY_PARAMS:
                return Response({"recipe_status": "running"});
            else:
                data = { "value": random.random() * 100}
                return Response(data);
        except Exception, e:
            handle_exception(e, request)
            

