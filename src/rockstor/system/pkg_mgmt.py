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
from datetime import (datetime, timedelta)

YUM = '/usr/bin/yum'
RPM = '/usr/bin/rpm'


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

def current_version():
    out, err, rc = run_command([RPM, '-qi', 'rockstor'], throw=False)
    if (rc != 0):
        return '0.0-0'
    return ('%s-%s' % (out[1].split(':')[-1].strip(),
                       out[2].split(':')[-1].strip()))

def rpm_build_info(pkg):
    version = None
    date = None
    o, e, rc = run_command([RPM, '-qi', pkg])
    for l in o:
        if (re.match('Build Date', l) is not None):
            #eg: Build Date  : Tue 11 Aug 2015 02:25:24 PM PDT
            #we return 2015-Aug-11
            dfields = l.strip().split()
            dstr = ' '.join(dfields[3:7])
            bdate = datetime.strptime(dstr, '%a %d %b %Y')
            bdate += timedelta(days=1)
            date = bdate.strftime('%Y-%b-%d')
        if (re.match('Version ', l) is not None):
            version = l.strip().split()[2]
        if (re.match('Release ', l) is not None):
            version = '%s-%s' % (version, l.strip().split()[2])
    return (version, date)

def update_check():
    pkg = 'rockstor'
    version, date = rpm_build_info(pkg)
    o, e, rc = run_command([YUM, 'changelog', date, pkg])
    log = False
    available = False
    new_version = None
    updates = []
    for l in o:
        if (re.search('Available Packages', l) is not None):
            available = True
        if (not available):
            continue
        if (new_version is None and (re.match('rockstor-', l) is not None)):
            new_version = l.split()[0].split('rockstor-')[1].split('.x86_64')[0]
        if (log is True):
            updates.append(l)
            if (len(l.strip()) == 0):
                log = False
        if (re.match('\* ', l) is not None):
            log = True
    if (new_version is None):
        new_version = version
    return (version, new_version, updates)


def update_run():
    fh, npath = mkstemp()
    with open(npath, 'w') as atfo:
        atfo.write('%s stop rockstor\n' % SYSTEMCTL)
        atfo.write('%s --setopt=timeout=600 -y update\n' % YUM)
        atfo.write('%s start rockstor\n' % SYSTEMCTL)
        atfo.write('/bin/rm -f %s\n' % npath)
    run_command([SYSTEMCTL, 'start', 'atd'])
    out, err, rc = run_command([AT, '-f', npath, 'now + 1 minutes'])
    time.sleep(120)
    return out, err, rc
