
import datetime
from smart_manager.models.nfsd import (NFSDCallDistribution,
                                       NFSDClientDistribution)
from django.utils.timezone import utc


def process_nfsd_calls(queue, output, ro, l):

    for line in output.split('\n'):
        fields = line.split()
        if (len(fields) < 9):
            l.info('ignoring incomplete sprobe output: %s' % repr(fields))
            continue
        fields[0] = datetime.datetime.fromtimestamp(float(fields[0])).replace(tzinfo=utc)
        fields.insert(0, ro)
        if (len(fields) == 11):
            queue.put(NFSDClientDistribution(*fields))
        else:
            no = NFSDCallDistribution(rid=fields[0], ts=fields[1],
                                      num_lookup=fields[2], num_read=fields[3],
                                      num_write=fields[4],
                                      num_create=fields[5],
                                      num_commit=fields[6],
                                      num_remove=fields[7], sum_read=fields[8],
                                      sum_write=fields[9])
            queue.put(no)
    return True


