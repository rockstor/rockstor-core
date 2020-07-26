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

import re
from rest_framework.response import Response
from django.db import transaction
from storageadmin.models import (
    Disk,
    SMARTInfo,
    SMARTAttribute,
    SMARTCapability,
    SMARTErrorLog,
    SMARTErrorLogSummary,
    SMARTTestLog,
    SMARTTestLogDetail,
    SMARTIdentity,
)
from storageadmin.serializers import SMARTInfoSerializer
from storageadmin.util import handle_exception
import rest_framework_custom as rfc
from system.smart import (
    extended_info,
    capabilities,
    info,
    error_logs,
    test_logs,
    run_test,
)
from datetime import datetime
from django.utils.timezone import utc

import logging

logger = logging.getLogger(__name__)


class DiskSMARTDetailView(rfc.GenericView):
    serializer_class = SMARTInfoSerializer

    @staticmethod
    def _validate_disk(did, request):
        try:
            return Disk.objects.get(id=did)
        except:
            e_msg = "Disk id ({}) does not exist.".format(did)
            handle_exception(Exception(e_msg), request)

    def get(self, *args, **kwargs):
        with self._handle_exception(self.request):
            disk = self._validate_disk(kwargs["did"], self.request)
            try:
                sinfo = SMARTInfo.objects.filter(disk=disk).order_by("-toc")[0]
                return Response(SMARTInfoSerializer(sinfo).data)
            except:
                return Response()

    @staticmethod
    @transaction.atomic
    def _info(disk):
        attributes = extended_info(disk.name, disk.smart_options)
        cap = capabilities(disk.name, disk.smart_options)
        e_summary, e_lines = error_logs(disk.name, disk.smart_options)
        smartid = info(disk.name, disk.smart_options)
        test_d, log_lines = test_logs(disk.name, disk.smart_options)
        ts = datetime.utcnow().replace(tzinfo=utc)
        si = SMARTInfo(disk=disk, toc=ts)
        si.save()
        for k in sorted(attributes.keys(), reverse=True):
            t = attributes[k]
            sa = SMARTAttribute(
                info=si,
                aid=t[0],
                name=t[1],
                flag=t[2],
                normed_value=t[3],
                worst=t[4],
                threshold=t[5],
                atype=t[6],
                updated=t[7],
                failed=t[8],
                raw_value=t[9],
            )
            sa.save()
        for c in sorted(cap.keys(), reverse=True):
            t = cap[c]
            SMARTCapability(info=si, name=c, flag=t[0], capabilities=t[1]).save()
        for enum in sorted(e_summary.keys(), key=int, reverse=True):
            l = e_summary[enum]
            SMARTErrorLogSummary(
                info=si,
                error_num=enum,
                lifetime_hours=l[0],
                state=l[1],
                etype=l[2],
                details=l[3],
            ).save()
        for l in e_lines:
            SMARTErrorLog(info=si, line=l).save()
        for tnum in sorted(test_d.keys()):
            t = test_d[tnum]
            tlen = len(t)
            if tlen < 5:
                [t.append("") for i in range(tlen, 5)]
            for i in range(2, 4):
                try:
                    t[i] = int(t[i])
                except:
                    t[i] = -1
            SMARTTestLog(
                info=si,
                test_num=tnum,
                description=t[0],
                status=t[1],
                pct_completed=t[2],
                lifetime_hours=t[3],
                lba_of_first_error=t[4],
            ).save()
        for l in log_lines:
            SMARTTestLogDetail(info=si, line=l).save()

        SMARTIdentity(
            info=si,
            model_family=smartid[0],
            device_model=smartid[1],
            serial_number=smartid[2],
            world_wide_name=smartid[3],
            firmware_version=smartid[4],
            capacity=smartid[5],
            sector_size=smartid[6],
            rotation_rate=smartid[7],
            in_smartdb=smartid[8],
            ata_version=smartid[9],
            sata_version=smartid[10],
            scanned_on=smartid[11],
            supported=smartid[12],
            enabled=smartid[13],
            version=smartid[14],
            assessment=smartid[15],
        ).save()
        return Response(SMARTInfoSerializer(si).data)

    def post(self, request, did, command):
        with self._handle_exception(request):
            disk = self._validate_disk(did, request)
            if command == "info":
                return self._info(disk)
            elif command == "test":
                test_type = request.data.get("test_type")
                if re.search("short", test_type, re.IGNORECASE) is not None:
                    test_type = "short"
                elif (
                    re.search("extended", test_type, re.IGNORECASE) is not None
                ):  # noqa E501
                    test_type = "long"
                elif (
                    re.search("conveyance", test_type, re.IGNORECASE) is not None
                ):  # noqa E501
                    test_type = "conveyance"
                else:
                    raise Exception(("Unsupported Self-Test: ({}).").format(test_type))
                run_test(disk.name, test_type, disk.smart_options)
                return self._info(disk)

            e_msg = (
                "Unknown command: ({}). The only valid commands are info and test."
            ).format(command)
            handle_exception(Exception(e_msg), request)
