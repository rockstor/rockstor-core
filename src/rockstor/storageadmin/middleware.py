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

from system.osi import run_command
from django.conf import settings

import logging

logger = logging.getLogger(__name__)


class ProdExceptionMiddleware(object):
    def process_exception(self, request, exception):
        """just log the exception"""
        e_msg = (
            "Exception occurred while processing a request. Path: {} method: {}"
        ).format(request.path, request.method)
        logger.error(e_msg)
        logger.exception(exception)
        run_command(
            [
                "/usr/bin/tar",
                "-c",
                "-z",
                "-f",
                settings.ROOT_DIR + "src/rockstor/logs/error.tgz",
                settings.ROOT_DIR + "var/log",
            ]
        )
