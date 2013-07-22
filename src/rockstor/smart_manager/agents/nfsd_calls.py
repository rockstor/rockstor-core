
import datetime
from smart_manager.models import (NFSDCallDistribution,
                                  NFSDClientDistribution,
                                  NFSDShareDistribution,
                                  NFSDShareClientDistribution)
from django.utils.timezone import utc

def get_datetime(ts):
    return datetime.datetime.utcfromtimestamp(float(ts)).replace(tzinfo=utc)

def process_nfsd_calls(queue, output, ro, l):

    for line in output.split('\n'):
        if (line == ''):
            continue
        fields = line.split()
        if (len(fields) < 9):
            l.info('ignoring incomplete sprobe output: %s' % repr(fields))
            continue
        fields[0] = get_datetime(fields[0])
        no = None
        if (len(fields) == 10):
            no = NFSDClientDistribution(rid=ro, ts=fields[0],
                                        ip=fields[1],
                                        num_lookup=fields[2],
                                        num_read=fields[3],
                                        num_write=fields[4],
                                        num_create=fields[5],
                                        num_commit=fields[6],
                                        num_remove=fields[7],
                                        sum_read=fields[8],
                                        sum_write=fields[9])
        else:
            no = NFSDCallDistribution(rid=ro, ts=fields[0],
                                      num_lookup=fields[1], num_read=fields[2],
                                      num_write=fields[3],
                                      num_create=fields[4],
                                      num_commit=fields[5],
                                      num_remove=fields[6], sum_read=fields[7],
                                      sum_write=fields[8])
        queue.put(no)
    return True

def share_distribution(queue, output, ro, l):

    for line in output.split('\n'):
        if (line == ''):
            continue
        fields = line.split()
        if (len(fields) < 10):
            l.info('ignoring incomplete sprobe output: %s' % repr(fields))
            continue
        no = NFSDShareDistribution(rid=ro, ts=get_datetime(fields[0]),
                                   share=fields[1], num_lookup=fields[2],
                                   num_read=fields[3], num_write=fields[4],
                                   num_create=fields[5], num_commit=fields[6],
                                   num_remove=fields[7], sum_read=fields[8],
                                   sum_write=fields[9])
        queue.put(no)
    return True

def share_client_distribution(queue, output, ro, l):

    for line in output.split('\n'):
        if (line == ''):
            continue
        fields = line.split()
        if (len(fields) < 10):
            l.info('ignoring incomplete sprobe output: %s' % repr(fields))
            continue
        no = NFSDShareClientDistribution(rid=ro, ts=get_datetime(fields[0]),
                                         share=fields[1], client=fields[2],
                                         num_lookup=fields[3],
                                         num_read=fields[4],
                                         num_write=fields[5],
                                         num_create=fields[6],
                                         num_commit=fields[7],
                                         num_remove=fields[8],
                                         sum_read=fields[9],
                                         sum_write=fields[10])
        queue.put(no)
    return True
