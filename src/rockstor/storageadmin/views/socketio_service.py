"""
Copyright (c) 2012-2013 RockStor, Inc. <http://rockstor.com>
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
from socketio.namespace import BaseNamespace
from socketio.mixins import BroadcastMixin
from socketio.sdjango import namespace

@namespace('')
class RockStorMessageNamespace(BaseNamespace, BroadcastMixin):

    def on_sm_data_update(self, sm_data):
        self.broadcast_event('sm_data', sm_data);

    #def broadcast_event(self, event, *args):
    #    """
    #    This is sent to all in the sockets (in this particular Namespace),
    #    including itself.
    #    """
    #    pkt = dict(type="event",
    #               name=event,
    #               args=args,
    #               endpoint=self.ns_name)

    #    for sessid, socket in self.socket.server.sockets.iteritems():
    #        socket.send_packet(pkt)
        
#def socketio_service(request):
#    print "in socketio_service"
#    socketio_manage(request.environ, {'': RockStorMessageNamespace}, request=request)
#    return {}


