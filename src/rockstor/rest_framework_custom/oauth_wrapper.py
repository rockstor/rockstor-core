"""
Copyright (c) 2012-2015 RockStor, Inc. <http://rockstor.com>
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

from oauth2_provider.ext.rest_framework import OAuth2Authentication


class RockstorOAuth2Authentication(OAuth2Authentication):

    def authenticate(self, request):
        # on success we get a (user, access_token) tuple.  if auth is
        # unsuccessful, we get None finally, the workaround case is when we get
        # the access_token but user is None(due to a bug/feature in
        # oauth2_provider). In this case, we set the user and return the tuple.
        creds = super(RockstorOAuth2Authentication, self).authenticate(request)
        if (creds is None or len(creds) != 2):
            return None
        user, access_token = creds
        if (user is None):
            user = access_token.application.user
        return user, access_token
