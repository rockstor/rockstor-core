"""
Copyright (c) 2012-2015 RockStor, Inc. <http://rockstor.com>
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
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import sys
from django.conf import settings
import zmq
from storageadmin.models import NetworkInterface
import logging
logger = logging.getLogger(__name__)


def main():
    rid = int(sys.argv[1])
    ctx = zmq.Context()
    #convert to request reply socket
    push_socket = ctx.socket(zmq.PUSH)
    ip = NetworkInterface.objects.filter(ipaddr__isnull=False)[0].ipaddr
    push_socket.connect('tcp://%s:%d' % (ip, settings.REPLICA_META_PORT))
    msg = {'id': rid,
           'msg': 'new_send', }
    push_socket.send_json(msg)
    ctx.destroy(linger=6000)

if __name__ == '__main__':
    #takes one argument. taskdef object id.
    main()
