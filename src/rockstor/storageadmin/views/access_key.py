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

"""
Oauth2 Access keys 
"""

from rest_framework.response import Response
from django.db import transaction
from oauth2_provider.models import Application as OauthApplication
from storageadmin.serializers import OauthApplicationSerializer
import rest_framework_custom as rfc

class AccessKeyView(rfc.GenericView):
    serializer_class = OauthApplicationSerializer

    def get_queryset(self, *args, **kwargs):
        if ('name' in kwargs):
            self.paginate_by = 0
            try:
                return OauthApplication.objects.get(name=kwargs['dname'])
            except:
                return []
        return OauthApplication.objects.all()

