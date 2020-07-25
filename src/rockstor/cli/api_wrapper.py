"""
Copyright (c) 2012-2020 RockStor, Inc. <http://rockstor.com>
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

import requests
import time
import json
import base64
from storageadmin.exceptions import RockStorAPIException
from storageadmin.models import OauthApp
from django.conf import settings


class APIWrapper(object):
    def __init__(self, client_id=None, client_secret=None, url=None):
        self.access_token = None
        self.expiration = time.time()
        self.client_id = client_id
        self.client_secret = client_secret
        # directly connect to gunicorn, bypassing nginx as we are on the same
        # host.
        self.url = "http://127.0.0.1:8000"
        if url is not None:
            # for remote urls.
            self.url = url

    def set_token(self):
        if self.client_id is None or self.client_secret is None:
            app = OauthApp.objects.get(name=settings.OAUTH_INTERNAL_APP)
            self.client_id = app.application.client_id
            self.client_secret = app.application.client_secret

        token_request_data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        user_pass = "{0}:{1}".format(self.client_id, self.client_secret)
        auth_string = base64.b64encode(user_pass.encode("utf-8"))
        auth_headers = {
            "HTTP_AUTHORIZATION": "Basic " + auth_string.decode("utf-8"),
        }
        content = None
        try:
            response = requests.post(
                "%s/o/token/" % self.url,
                data=token_request_data,
                headers=auth_headers,
                verify=False,
            )
            content = json.loads(response.content.decode("utf-8"))
            self.access_token = content["access_token"]
            self.expiration = int(time.time()) + content["expires_in"] - 600
        except Exception as e:
            msg = (
                "Exception while setting access_token for url(%s): %s. "
                "content: %s" % (self.url, e.__str__(), content)
            )
            raise Exception(msg)

    def api_call(self, url, data=None, calltype="get", headers=None, save_error=True):
        if self.access_token is None or time.time() > self.expiration:
            self.set_token()

        api_auth_header = {
            "Authorization": "Bearer " + self.access_token,
        }
        call = getattr(requests, calltype)
        url = "%s/api/%s" % (self.url, url)
        try:
            if headers is not None:
                headers.update(api_auth_header)
                if headers["content-type"] == "application/json":
                    r = call(url, verify=False, data=json.dumps(data), headers=headers)
                else:
                    r = call(url, verify=False, data=data, headers=headers)
            else:
                r = call(url, verify=False, headers=api_auth_header, data=data)
        except requests.exceptions.ConnectionError:
            print("Error connecting to Rockstor. Is it running?")
            raise

        if r.status_code == 404:
            msg = "Invalid api end point: %s" % url
            raise RockStorAPIException(detail=msg)

        if r.status_code != 200:
            try:
                error_d = json.loads(r.text)
                if settings.DEBUG is True and save_error is True:
                    cur_time = str(int(time.time()))
                    err_file = "/tmp/err-%s.html" % cur_time
                    with open(err_file, "w") as efo:
                        for line in r.text.split("\n"):
                            efo.write("%s\n" % line)
                        print("Error detail is saved at %s" % err_file)
                if "detail" in error_d:
                    if (
                        error_d["detail"]
                        == "Authentication credentials were not provided."
                    ):  # noqa E501
                        self.set_token()
                        return self.api_call(
                            url,
                            data=data,
                            calltype=calltype,
                            headers=headers,
                            save_error=save_error,
                        )
                    raise RockStorAPIException(detail=error_d["detail"])
            except ValueError as e:
                raise RockStorAPIException(
                    detail="Internal Server Error: %s" % e.__str__()
                )
            r.raise_for_status()

        try:
            ret_val = r.json()
        except ValueError:
            ret_val = {}
        return ret_val
