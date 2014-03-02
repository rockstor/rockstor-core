"""
Copyright (c) 2012-2014 RockStor, Inc. <http://rockstor.com>
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

from multiprocessing import Process
import os
import time
import sys
from contextlib import contextmanager
import subprocess
from backup.util import (update_trail, mount_source, create_snapshot)
from django.conf import settings
from system.osi import is_share_mounted
from fs.btrfs import mount_share

import logging
logger = logging.getLogger(__name__)

RSYNC = '/usr/bin/rsync'


class BackupPluginWorker(Process):

    def __init__(self, po, to, dest_pool):
        self.ppid = os.getpid()
        self.tid = to['id']
        self.source_ip = po.source_ip
        self.source_path = po.source_path
        self.dest_share = po.dest_share
        self.dest_pool = dest_pool
        super(BackupPluginWorker, self).__init__()

    @contextmanager
    def _clean_exit_handler(self, msg):
        try:
            yield
        except Exception, e:
            logger.error(msg)
            logger.exception(e)
            sys.exit(3)

    @contextmanager
    def _update_trail_and_quit(self, msg, data=None):
        try:
            yield
        except Exception, e:
            logger.error(msg)
            logger.exception(e)
            try:
                data = {'status': 'failed',
                        'error': msg,}
                update_trail(self.tid, data, logger)
            except Exception, e:
                logger.error('Exception occured in cleanup handler')
                logger.exception(e)
            finally:
                sys.exit(-1)
        finally:
            if (data is not None):
                logger.debug('updating trail(%d) with data(%s)' % (self.tid,
                                                                   data))
                try:
                    update_trail(self.tid, data, logger)
                except Exception, e:
                    logger.error('Exception occured while updating trail')
                    logger.exception(e)
                    sys.exit(-1)

    def run(self):
        #0. mount destination share
        mnt_pt = ('%s/%s' % (settings.MNT_PT, self.dest_share))
        msg = ('Destination share(%s) not mounted' % self.dest_share)
        with self._update_trail_and_quit(msg):
            if (not is_share_mounted(self.dest_share)):
                mount_share(self.dest_share, self.dest_pool, mnt_pt)
            if (not is_share_mounted(self.dest_share)):
                raise Exception(msg)

        #1. if not mounted, mount
        msg = ('Failed to mount source(%s:%s)' % (self.source_ip,
                                                  self.source_path))
        with self._update_trail_and_quit(msg):
            mount_source(self.source_ip, self.source_path)

        #2. create a snapshot
        snap_name = ('snap-%d' % self.tid)
        msg = ('Failed to create snapshot(%s) for share(%s)' %
               (snap_name, self.dest_share))
        data = {'status': 'snapshot created',}
        with self._update_trail_and_quit(msg, data=data):
            create_snapshot(self.dest_share, snap_name, logger)

        #3. rsync
        src_mnt = ('/mnt/backup/%s_%s' % (self.source_ip, self.source_path))
        dest_mnt = ('/mnt2/%s' % self.dest_share)
        cmd = [RSYNC, '-az', src_mnt, dest_mnt]
        msg = ('Unable to start sync')
        data = {'status': 'sync started',}
        with self._update_trail_and_quit(msg, data=data):
            rp = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        while True:
            if (os.getppid() != self.ppid):
                msg = ('Parent process exited. Aborting')
                with self._update_trail_and_quit(msg):
                    rp.terminate()

            if (rp.poll() is not None):
                msg = ('sync finished. But failed to update trail status')
                data = {'status': 'succeeded',}
                with self._update_trail_and_quit(msg, data):
                    logger.debug('sync finished')
                break
            logger.debug('rsync still running')
