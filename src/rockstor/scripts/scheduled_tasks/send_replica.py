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

import sys
from django.conf import settings
import zmq
import logging

logger = logging.getLogger(__name__)


def main():
    rid = int(sys.argv[1])
    ctx = zmq.Context()
    poll = zmq.Poller()
    num_tries = 12
    while True:
        req = ctx.socket(zmq.DEALER)
        poll.register(req, zmq.POLLIN)
        req.connect("ipc://%s" % settings.REPLICATION.get("ipc_socket"))
        req.send_multipart(["new-send", b"%d" % rid])

        socks = dict(poll.poll(5000))
        if socks.get(req) == zmq.POLLIN:
            rcommand, reply = req.recv_multipart()
            if rcommand == "SUCCESS":
                print(reply)
                break
            ctx.destroy(linger=0)
            sys.exit(reply)
        num_tries -= 1
        print(
            "No response from Replication service. Number of retry "
            "attempts left: %d" % num_tries
        )
        if num_tries == 0:
            ctx.destroy(linger=0)
            sys.exit(
                "Check that Replication service is running properly and try again."
            )
        req.setsockopt(zmq.LINGER, 0)
        req.close()
        poll.unregister(req)

    ctx.destroy(linger=0)
    sys.exit(0)


if __name__ == "__main__":
    # takes one argument. taskdef object id.
    main()
