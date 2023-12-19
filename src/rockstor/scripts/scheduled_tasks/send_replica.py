"""
Copyright (c) 2012-2023 RockStor, Inc. <https://rockstor.com>
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
along with this program. If not, see <https://www.gnu.org/licenses/>.
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
    num_tries = 3
    while True:
        req = ctx.socket(zmq.DEALER)
        print(f"req = {req}")
        poll.register(req, zmq.POLLIN)
        print(f"poll.register = {poll.register}")
        ipc_socket = settings.REPLICATION.get('ipc_socket')
        req.connect(f"ipc://{ipc_socket}")
        print(f"req.connect = {req.connect}, ipc_socket = {ipc_socket}")
        req.send_multipart([b"new-send", f"{rid}".encode('utf-8')])

        socks = dict(poll.poll(5000))
        # print(f"socks.get(req) = {socks.get(req)}")
        if socks.get(req) == zmq.POLLIN:
            rcommand, reply = req.recv_multipart()
            print(f"rcommand={rcommand}, reply={reply}")
            if rcommand == b"SUCCESS":
                print(reply)
                break
            ctx.destroy(linger=0)
            sys.exit(reply)
        num_tries -= 1
        print(
            "No response from Replication service. Number of retry "
            f"attempts left: {num_tries}"
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
