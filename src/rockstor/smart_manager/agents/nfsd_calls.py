import datetime
from smart_manager.models import (
    NFSDCallDistribution,
    NFSDClientDistribution,
    NFSDShareDistribution,
    NFSDShareClientDistribution,
    SProbe,
    NFSDUidGidDistribution,
)
from django.utils.timezone import utc


def get_datetime(ts):
    return datetime.datetime.utcfromtimestamp(float(ts)).replace(tzinfo=utc)


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
