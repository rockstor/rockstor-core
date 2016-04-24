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

from django.http import HttpResponse
from storageadmin.util import handle_exception
import rest_framework_custom as rfc
from django.conf import settings
from subprocess import check_output

import logging
logger = logging.getLogger(__name__)

readers = {'cat' : {'command' : '/usr/bin/cat', 'args' : '-n'},
           'tail' : {'command' : '/usr/bin/tail', 'args' : '-n 30'},
}

system_logs = '/var/log/'
rockstor_logs = '%svar/log/' % settings.ROOT_DIR
samba_subd_logs = '%ssamba/' % system_logs
nginx_subd_logs = '%snginx/' % system_logs

logs = {'rockstor' : '%srockstor.log' % rockstor_logs,
        'dmesg' : '%sdmesg' % system_logs,
        'nmbd' : '%slog.nmbd' % samba_subd_logs,
        'smbd' : '%slog.smbd' % samba_subd_logs,
        'winbindd' : '%slog.winbindd' % samba_subd_logs,
        'nginx' : '%saccess.log' % nginx_subd_logs,
        'yum' : '%syum.log' % system_logs,
}

class LogsReaderView(rfc.GenericView):

     def get(self, request, read_type, logs_options):
        #HttpResponse used to return a plain text instead of a serialized/jsonified text 
        log_text = check_output([readers[read_type]['command'], readers[read_type]['args'], logs[logs_options]])
        return HttpResponse(log_text, content_type='text/plain')
