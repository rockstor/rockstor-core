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

import os
import requests
import time
import json
import base64
from storageadmin.exceptions import RockStorAPIException
from functools import wraps
from base_console import BaseConsole
from storageadmin.models import OauthApp
from django.conf import settings

API_TOKEN = None


def set_token(client_id=None, client_secret=None, url=None, logger=None):
    if client_id is None or client_secret is None or url is None:
        os.environ["DJANGO_SETTINGS_MODULE"] = "settings"
        app = OauthApp.objects.get(name=settings.OAUTH_INTERNAL_APP)
        client_id = app.client_id()
        client_secret = app.client_secret()
        url = "https://localhost"

    token_request_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    user_pass = "{0}:{1}".format(client_id, client_secret)
    auth_string = base64.b64encode(user_pass.encode("utf-8"))
    auth_headers = {
        "HTTP_AUTHORIZATION": "Basic " + auth_string.decode("utf-8"),
    }
    response = requests.post(
        "%s/o/token/" % url, data=token_request_data, headers=auth_headers, verify=False
    )
    try:
        content = json.loads(response.content.decode("utf-8"))
        global API_TOKEN
        API_TOKEN = content["access_token"]
        return API_TOKEN
    except Exception as e:
        if logger is not None:
            logger.exception(e)
        msg = (
            "Exception while setting access_token for url(%s). Make sure "
            "credentials are correct: %s" % (url, e.__str__())
        )
        raise Exception(msg)


def api_error(console_func):
    @wraps(console_func)
    def arg_wrapper(a1, a2):
        try:
            return console_func(a1, a2)
        except RockStorAPIException as e:
            print(
                "Operation failed due to the following error returned "
                "from the server:"
            )
            print("-----------------------------------------")
            print(e.detail)
            print("-----------------------------------------")
            return -1

    return arg_wrapper


def api_call(url, data=None, calltype="get", headers=None, save_error=True):
    if API_TOKEN is None:
        set_token()
    api_auth_header = {
        "Authorization": "Bearer " + API_TOKEN,
    }
    call = getattr(requests, calltype)
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
        return {}

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
                    error_d["detail"] == "Authentication credentials were not provided."
                ):  # noqa E501
                    set_token()
                    return api_call(
                        url,
                        data=data,
                        calltype=calltype,
                        headers=headers,
                        save_error=save_error,
                    )
                raise RockStorAPIException(detail=error_d["detail"])
        except ValueError:
            raise RockStorAPIException(detail="Internal Server Error")
        r.raise_for_status()

    try:
        ret_val = r.json()
    except ValueError:
        ret_val = {}
    return ret_val


def print_pools_info(pools_info):
    if pools_info is None or not isinstance(pools_info, dict) or len(pools_info) == 0:
        print("There are no pools on the appliance.")
        return
    try:
        if "count" not in pools_info:
            pools_info = [pools_info]
        else:
            pools_info = pools_info["results"]
        print("%(c)sPools on the appliance\n%(e)s" % BaseConsole.c_params)
        print("Name\tSize\tFree\tReclaimable\tRaid")
        for p in pools_info:
            print_pool_info(p)
    except Exception as e:
        print(e)
        print("Error displaying pool info")


def print_pool_info(p, header=False):
    try:
        if header:
            print("%(c)sPool info%(e)s\n" % BaseConsole.c_params)
            print("Name\tSize\tFree\tReclaimable\tRaid")
        p["size"] = sizeof_fmt(p["size"])
        p["free"] = sizeof_fmt(p["free"])
        p["reclaimable"] = sizeof_fmt(p["reclaimable"])
        print(
            "%s%s%s\t%s\t%s\t%s\t%s"
            % (
                BaseConsole.c,
                p["name"],
                BaseConsole.e,
                p["size"],
                p["free"],
                p["reclaimable"],
                p["raid"],
            )
        )
    except Exception as e:
        print(e)
        print("Error displaying pool info")


def print_scrub_status(pool_name, scrub_info):
    try:
        print("%sScrub status for %s%s" % (BaseConsole.c, pool_name, BaseConsole.e))
        kb_scrubbed = None
        if "kb_scrubbed" in scrub_info:
            kb_scrubbed = scrub_info["kb_scrubbed"]
        status = scrub_info["status"]
        print("%sStatus%s:  %s" % (BaseConsole.c, BaseConsole.e, status))
        if status == "finished":
            print("%sKB Scrubbed%s:  %s" % (BaseConsole.c, BaseConsole.e, kb_scrubbed))
    except Exception as e:
        print(e)
        print("Error displaying scrub status")


def print_shares_info(shares):
    if shares is None or not isinstance(shares, dict) or len(shares) == 0:
        print("There are no shares in the system")
        return
    try:
        if "count" not in shares:
            shares = [shares]
        else:
            shares = shares["results"]
        print("%(c)sShares on the appliance%(e)s\n" % BaseConsole.c_params)
        print("Name\tSize(KB)\tUsage(KB)\tPool")
        for s in shares:
            print_share_info(s)
    except Exception as e:
        print(e)
        print("Error displaying share info")


def print_share_info(s, header=False):
    try:
        if header:
            print("%(c)sShare info%(e)s\n" % BaseConsole.c_params)
            print("Name\tSize(KB)\tUsage(KB)\tPool")
        print(
            "%s\t%s\t%s\t%s" % (s["name"], s["size"], s["r_usage"], s["pool"]["name"])
        )
    except Exception as e:
        print(e)
        print("Error displaying share info")


def print_disks_info(disks_info):
    if disks_info is None or not isinstance(disks_info, dict) or len(disks_info) == 0:
        print("There are no disks on the appliance.")
        return
    try:
        if "results" not in disks_info:
            #  POST is used, don't do anything
            disks_info = disks_info
        elif "count" not in disks_info:
            disks_info = [disks_info]
        else:
            disks_info = disks_info["results"]
        print("%sDisks on this Rockstor appliance%s\n" % (BaseConsole.u, BaseConsole.e))
        print("Name\tSize\tPool")
        for d in disks_info:
            print_disk_info(d)
    except Exception as e:
        print(e)
        print("Error displaying disk info")


def print_disk_info(d, header=False):
    try:
        if header:
            print("%(u)sDisk info%(e)s\n" % BaseConsole.c_params)
            print("Name\tSize\tPool")
        d["size"] = sizeof_fmt(d["size"])
        print(
            "%s%s%s\t%s\t%s"
            % (BaseConsole.c, d["name"], BaseConsole.e, d["size"], d["pool_name"])
        )
    except Exception as e:
        print(e)
        print("Error displaying disk info")


def print_export_info(export_info):
    if (
        export_info is None
        or not isinstance(export_info, dict)
        or len(export_info) == 0
    ):
        print("%(c)sThere are no exports for this share%(e)s" % BaseConsole.c_params)
        return
    try:
        if "count" not in export_info:
            export_info = [export_info]
        else:
            export_info = export_info["results"]
        if len(export_info) == 0:
            print(
                "%(c)sThere are no exports for this share%(e)s" % BaseConsole.c_params
            )
        else:
            print("%(c)sList of exports for this share%(e)s" % BaseConsole.c_params)
            print("Id\tMount\tClient\tWritable\tSyncable\tEnabled")
            for e in export_info:
                print(
                    "%s\t%s\t%s\t%s\t%s\t%s"
                    % (
                        e["id"],
                        e["exports"][0]["mount"],
                        e["host_str"],
                        e["editable"],
                        e["syncable"],
                        e["enabled"],
                    )
                )
    except Exception as e:
        print(e)
        print("Error displaying nfs export information")


def sizeof_fmt(num):
    for x in ["K", "M", "G", "T", "P", "E"]:
        if num < 0.00:
            num = 0
            break
        if num < 1024.00:
            break
        else:
            num /= 1024.00
            x = "Z"
    return "%3.2f%s" % (num, x)
