"""
Copyright (joint work) 2024 The Rockstor Project <https://rockstor.com>

Rockstor is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

Rockstor is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

from django.db import models
from oauth2_provider.models import Application
from storageadmin.models import User
from settings import OAUTH_INTERNAL_APP, CLIENT_SECRET


class OauthApp(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE)
    name = models.CharField(max_length=128, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def client_id(self, *args, **kwargs):
        return self.application.client_id

    def client_secret(self, *args, **kwargs):
        # For our internal app, we return our 'pass' secret:
        if self.application.name == OAUTH_INTERNAL_APP:
            return CLIENT_SECRET
        return self.application.client_secret

    @property
    def is_internal(self, *args, **kwargs):
        if self.application.name == OAUTH_INTERNAL_APP:
            return True
        return False

    class Meta:
        app_label = "storageadmin"
        ordering = ['-id']
