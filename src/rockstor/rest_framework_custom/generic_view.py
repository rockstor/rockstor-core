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

from rest_framework.generics import ListCreateAPIView
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication,)
from storageadmin.auth import DigestAuthentication
from rest_framework.permissions import IsAuthenticated
from oauth_wrapper import RockstorOAuth2Authentication
from contextlib import contextmanager
from storageadmin.util import handle_exception
from storageadmin.exceptions import RockStorAPIException


# TODO: Only allow put, and patch where necessary. This works right now
class GenericView(ListCreateAPIView):
    authentication_classes = (DigestAuthentication, SessionAuthentication,
                              BasicAuthentication,
                              RockstorOAuth2Authentication,)
    permission_classes = (IsAuthenticated, )

    @staticmethod
    @contextmanager
    def _handle_exception(request, msg=None):
        try:
            yield
        except RockStorAPIException:
            raise
        except Exception as e:
            handle_exception(e, request, msg)
