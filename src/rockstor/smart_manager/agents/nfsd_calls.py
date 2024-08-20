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
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

from datetime import datetime, timezone
from smart_manager.models import (
    NFSDCallDistribution,
    NFSDClientDistribution,
    NFSDShareDistribution,
    NFSDShareClientDistribution,
    SProbe,
    NFSDUidGidDistribution,
)


def get_datetime(ts):
    return datetime.datetime.utcfromtimestamp(float(ts)).replace(tzinfo=timezone.utc)


def process_nfsd_calls(output, rid, l):

    ro = SProbe.objects.get(id=rid)
    for line in output.split("\n"):
        if line == "":
            continue
        fields = line.split()
        if len(fields) < 9:
            l.info("ignoring incomplete sprobe output: %s" % repr(fields))
            continue
        fields[0] = get_datetime(fields[0])
        no = None
        if len(fields) == 10:
            no = NFSDClientDistribution(
                rid=ro,
                ts=fields[0],
                ip=fields[1],
                num_lookup=fields[2],
                num_read=fields[3],
                num_write=fields[4],
                num_create=fields[5],
                num_commit=fields[6],
                num_remove=fields[7],
                sum_read=fields[8],
                sum_write=fields[9],
            )
        else:
            no = NFSDCallDistribution(
                rid=ro,
                ts=fields[0],
                num_lookup=fields[1],
                num_read=fields[2],
                num_write=fields[3],
                num_create=fields[4],
                num_commit=fields[5],
                num_remove=fields[6],
                sum_read=fields[7],
                sum_write=fields[8],
            )
        no.save()


def share_distribution(output, rid, l):

    ro = SProbe.objects.get(id=rid)
    for line in output.split("\n"):
        if line == "":
            continue
        fields = line.split()
        if len(fields) < 10:
            l.info("ignoring incomplete sprobe output: %s" % repr(fields))
            continue
        no = NFSDShareDistribution(
            rid=ro,
            ts=get_datetime(fields[0]),
            share=fields[1],
            num_lookup=fields[2],
            num_read=fields[3],
            num_write=fields[4],
            num_create=fields[5],
            num_commit=fields[6],
            num_remove=fields[7],
            sum_read=fields[8],
            sum_write=fields[9],
        )
        no.save()


def share_client_distribution(output, rid, l):

    ro = SProbe.objects.get(id=rid)
    for line in output.split("\n"):
        if line == "":
            continue
        fields = line.split()
        if len(fields) < 11:
            l.info("ignoring incomplete sprobe output: %s" % repr(fields))
            continue
        no = NFSDShareClientDistribution(
            rid=ro,
            ts=get_datetime(fields[0]),
            share=fields[1],
            client=fields[2],
            num_lookup=fields[3],
            num_read=fields[4],
            num_write=fields[5],
            num_create=fields[6],
            num_commit=fields[7],
            num_remove=fields[8],
            sum_read=fields[9],
            sum_write=fields[10],
        )
        no.save()


def nfs_uid_gid_distribution(output, rid, l):

    ro = SProbe.objects.get(id=rid)
    for line in output.split("\n"):
        if line == "":
            continue
        fields = line.split()
        if len(fields) < 13:
            l.info("ignoring incomplete sprobe output: %s" % repr(fields))
            continue
        no = NFSDUidGidDistribution(
            rid=ro,
            ts=get_datetime(fields[0]),
            share=fields[1],
            client=fields[2],
            uid=fields[3],
            gid=fields[4],
            num_lookup=fields[5],
            num_read=fields[6],
            num_write=fields[7],
            num_create=fields[8],
            num_commit=fields[9],
            num_remove=fields[10],
            sum_read=fields[11],
            sum_write=fields[12],
        )
        no.save()
