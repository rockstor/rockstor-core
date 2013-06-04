
import datetime
from smart_manager.models.nfsd import (NFSDCallDistribution,
                                       NFSDClientDistribution)
from django.utils.timezone import utc


def process_nfsd_calls(queue, output, ro, l):

    for line in output.split('\n'):
        if (line == ''):
            continue
        fields = line.split()
        if (len(fields) < 9):
            l.info('ignoring incomplete sprobe output: %s' % repr(fields))
            continue
        fields[0] = datetime.datetime.fromtimestamp(float(fields[0])).replace(tzinfo=utc)
        if (len(fields) == 10):
            no = NFSDClientDistribution(rid=ro, ts=fields[0],
                                        num_lookup=fields[1],
                                        num_read=fields[2],
                                        num_write=fields[3],
                                        num_create=fields[4],
                                        num_commit=fields[5],
                                        num_remove=fields[6],
                                        sum_read=fields[7],
                                        sum_write=fields[8])
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


