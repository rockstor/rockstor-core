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
from osi import run_command
from services import systemctl
import shutil
import time
from datetime import (datetime, timedelta)
import requests
from django.conf import settings

YUM = '/usr/bin/yum'
RPM = '/usr/bin/rpm'
SYSTEMCTL = '/usr/bin/systemctl'
AT = '/usr/bin/at'
YCFILE = '/etc/yum/yum-cron.conf'


def install_pkg(name):
    return run_command([YUM, '--setopt=timeout=600', '-y', 'install', name])


def downgrade_pkgs(*packages):
    cmd = [YUM, '--setopt=timeout=600', '-y', 'downgrade', ]
    for p in packages:
        cmd.append(p)
    return run_command(cmd)


def auto_update(enable=True):
    service = 'yum-cron'
    fo, npath = mkstemp()
    updated = False
    with open(YCFILE) as ifo, open(npath, 'w') as tfo:
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
                        'is corrupt. No change made.' % YCFILE)
    shutil.move(npath, YCFILE)
    if (enable):
        systemctl(service, 'enable')
        systemctl(service, 'start')
    else:
        systemctl(service, 'stop')
        systemctl(service, 'disable')


def auto_update_status():
    enabled = False
    with open(YCFILE) as ifo:
        for line in ifo.readlines():
            if (re.match('apply_updates = yes', line) is not None):
                enabled = True
                break
    if (enabled):
        systemctl('yum-cron', 'status')
    return enabled


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
            # eg: Build Date  : Tue 11 Aug 2015 02:25:24 PM PDT
            # we return 2015-Aug-11
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


def switch_repo(subscription, on=True):
    yum_file = '/etc/yum.repos.d/Rockstor-%s.repo' % subscription.name
    if (on):
        with open(yum_file, 'w') as rfo:
            rfo.write('[Rockstor-%s]\n' % subscription.name)
            rfo.write('name=%s\n' % subscription.description)
            if (subscription.password is not None):
                rfo.write('baseurl=http://%s:%s@%s\n' %
                          (subscription.appliance.uuid, subscription.password,
                           subscription.url))
            else:
                rfo.write('baseurl=http://%s\n' % subscription.url)
            rfo.write('enabled=1\n')
            rfo.write('gpgcheck=1\n')
            rfo.write('gpgkey=file://%sconf/ROCKSTOR-GPG-KEY\n'
                      % settings.ROOT_DIR)
            rfo.write('metadata_expire=1m\n')
        os.chmod(yum_file, 600)
    else:
        if (os.path.exists(yum_file)):
            os.remove(yum_file)


def repo_status(subscription):
    if (subscription.password is None):
        return ('active', 'public repo')

    try:
        res = requests.get('http://%s' % subscription.url,
                           auth=(subscription.appliance.uuid,
                                 subscription.password))
        if (res.status_code == 401):
            return ('inactive', res.text)
        elif (res.status_code == 200):
            return ('active', res.text)
        return (res.status_code, res.text)
    except requests.ConnectionError as e:
        e_msg = ('Failed to connect to %s. Is the Rockstor system connected '
                 'to the internet?. Lower level exception: %s'
                 % (subscription.url, e.__str__()))
        raise Exception(e_msg)


def update_check(subscription=None):
    if (subscription is not None):
        switch_repo(subscription)

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
            new_version = l.split()[0].split(
                'rockstor-')[1].split('.x86_64')[0]
        if (log is True):
            updates.append(l)
            if (len(l.strip()) == 0):
                log = False
        if (re.match('\* ', l) is not None):
            log = True
    if (new_version is None):
        new_version = version
        # do a second check which is valid for updates without changelog
        # updates. eg: same day updates, testing updates.
        o, e, rc = run_command([YUM, 'update', pkg, '--assumeno'], throw=False)
        if (rc == 1):
            for l in o:
                if (re.search('will be an update', l) is not None):
                    if (re.search('rockstor.x86_64', l) is not None):
                        new_version = l.strip().split()[3].split(':')[1]

    return (version, new_version, updates)


def update_run(subscription=None):
    if (subscription is not None):
        switch_repo(subscription)

    run_command([SYSTEMCTL, 'start', 'atd'])
    fh, npath = mkstemp()
    with open(npath, 'w') as atfo:
        atfo.write('%s stop rockstor\n' % SYSTEMCTL)
        atfo.write('/usr/bin/find %s -name "*.pyc" -type f -delete\n'
                   % settings.ROOT_DIR)
        atfo.write('%s --setopt=timeout=600 -y update\n' % YUM)
        atfo.write('%s start rockstor\n' % SYSTEMCTL)
        atfo.write('/bin/rm -f %s\n' % npath)
    out, err, rc = run_command([AT, '-f', npath, 'now + 1 minutes'])
    time.sleep(120)

    return out, err, rc

def pkg_changelog(package):
    # Retrieve yum packages changelog, no update_check func
    # update_check is "Rockstor specific" and with standard CentOS packages
    # we can't work with rpm -qi Build Date field: some packages have
    # Build Date > new package version changelog
    # pkg_changelog behaviour is output beautify too, returning pkg name,
    # changelog for installed package and available new package update
    out, err, rc = run_command([YUM, 'changelog', '1', package], throw=False)
    package_info = {'name': package.split('.')[0]}
    package_info['installed'] = []
    package_info['available'] = []
    installed = False
    available = False
    for l in out:
        l = l.strip()
        if (re.search('Available Packages', l) is not None):
            installed = False
            available = True
            continue
        if (re.search('Installed Packages', l) is not None):
            installed = True
            continue
        if (re.search('changelog stats', l) is not None):
            installed = False
            available = False
            break
        if (installed and len(l) != 0):
            package_info['installed'].append(l)
        if (available and len(l) != 0):
            package_info['available'].append(l)

    package_info['installed'] = ''.join(package_info['installed'])
    package_info['available'] = ''.join(package_info['available'])

    return package_info

def yum_check():
    # Query yum for updates and grab return code
    # yum check-update retun code is 0 with no updates
    # and 100 if at least 1 update available
    out, err, rc = run_command([YUM, 'check-update', '-q'], throw=False)
    packages = []
    # Read check-update output skipping first and last empty line
    # on every round we apply some beautify with pkg_changelog
    for line in out[1:-1]:
        packages.append(pkg_changelog(line.split()[0].strip()))

    return rc, packages
