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

from rest_framework.response import Response
from rest_framework.views import APIView
from storageadmin.models import Appliance
from storageadmin.util import handle_exception
from cli.api_wrapper import APIWrapper


class ReceiverPoolListView(APIView):
    def get(self, *args, **kwargs):
        try:
            auuid = self.kwargs.get("auuid", None)
            ao = Appliance.objects.get(uuid=auuid)
            url = "https://%s:%s" % (ao.ip, ao.mgmt_port)
            aw = APIWrapper(
                client_id=ao.client_id, client_secret=ao.client_secret, url=url
            )
            response = aw.api_call("pools")
            res = [p["name"] for p in response["results"]]
            return Response(res)
        except Appliance.DoesNotExist:
            msg = "Remote appliance with the given uuid(%s) does not exist." % auuid
            handle_exception(Exception(msg), self.request)
        except Exception as e:
            msg = (
                "Failed to retrieve list of Pools on the remote "
                "appliance(%s). Make sure it is running and try again. "
                "Here is the exact error: %s" % (ao.ip, e.__str__())
            )
            handle_exception(Exception(msg), self.request)
