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

import os
import re
from tempfile import mkstemp
from shutil import move
from osi import run_command
from services import systemctl
import shutil

YUM = '/usr/bin/yum'


def install_pkg(name):
    return run_command([YUM, '--setopt=timeout=600', '-y', 'install', name])

def auto_update(enable=True):
    cfile = '/etc/yum/yum-cron.conf'
    service = 'yum-cron'
    fo, npath = mkstemp()
    updated = False
    with open(cfile) as ifo, open(npath, 'w') as tfo:
        for line in ifo.readlines():
            if (re.match('apply_updates = ', line) is not None):
                if (enable):
                    tfo.write('apply_updates = yes\n')
                else:
                    tfo.write('apply_updates = no\n')
                updated = True
            else:
                tfo.write(line)
    if (not updated):
        raise Exception('apply_updates directive missing in %s, assuming its '
                        'is corrupt. No change made.' % cfile)
    shutil.move(npath, cfile)
    if (enable):
        systemctl(service, 'enable')
        systemctl(service, 'start')
    else:
        systemctl(service, 'stop')
        systemctl(service, 'disable')
