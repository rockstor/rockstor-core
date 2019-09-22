"""
Copyright (c) 2012-2017 RockStor, Inc. <http://rockstor.com>
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
import stat
from tempfile import mkstemp
from osi import run_command
from services import systemctl
import shutil
import time
from datetime import (datetime, timedelta)
import requests
from django.conf import settings
from system.exceptions import CommandException
import distro
import logging

logger = logging.getLogger(__name__)

YUM = '/usr/bin/yum'
RPM = '/usr/bin/rpm'
SYSTEMCTL = '/usr/bin/systemctl'
AT = '/usr/bin/at'
YCFILE = '/etc/yum/yum-cron.conf'  # Doesn't exist in openSUSE


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
    version = 'Unknown Version'
    date = None
    try:
        o, e, rc = run_command([YUM, 'info', 'installed', '-v', pkg])
    except CommandException as e:
        # Catch "No matching Packages to list" so we can return None, None.
        emsg = 'Error: No matching Packages to list'
        # By checking both the first error element and the second to last we
        # catch one yum waiting for another to release yum lock.
        if e.err[0] == emsg or e.err[-2] == emsg:
            logger.info('No "rockstor" package found: source install?')
            return version, date
        # otherwise we raise an exception as normal.
        raise e
    for l in o:
        if (re.match('Buildtime', l) is not None):
            # eg: "Buildtime   : Tue Dec  5 13:34:06 2017"
            # we return 2017-Dec-06
            # Note the one day on from retrieved Buildtime with zero padding.
            dfields = l.strip().split()
            dstr = dfields[6] + ' ' + dfields[3] + ' ' + dfields[4]
            bdate = datetime.strptime(dstr, '%Y %b %d')
            bdate += timedelta(days=1)
            date = bdate.strftime('%Y-%b-%d')
        if (re.match('Version ', l) is not None):
            version = l.strip().split()[2]
        if (re.match('Release ', l) is not None):
            version = '%s-%s' % (version, l.strip().split()[2])
    return version, date


def switch_repo(subscription, on=True):
    repos_dir = '/etc/yum.repos.d'
    yum_file = '{}/Rockstor-{}.repo'.format(repos_dir, subscription.name)
    # Historically our base subscription url denotes our CentOS rpm repo.
    subscription_distro_url = subscription.url
    distro_id = distro.id()
    if distro_id == 'opensuse-leap':
        subscription_distro_url += '/leap/{}'.format(distro.version())
    elif distro_id == 'opensuse-tumbleweed':
        subscription_distro_url += '/tumbleweed'
    # Check if dir /etc/yum.repos.d exists and if not create.
    if not os.path.isdir(repos_dir):
        # Can use os.makedirs(path) if intermediate levels also don't exist.
        os.mkdir(repos_dir, )
    if (on):
        with open(yum_file, 'w') as rfo:
            rfo.write('[Rockstor-%s]\n' % subscription.name)
            rfo.write('name=%s\n' % subscription.description)
            if (subscription.password is not None):
                rfo.write('baseurl=http://%s:%s@%s\n' %
                          (subscription.appliance.uuid, subscription.password,
                           subscription_distro_url))
            else:
                rfo.write('baseurl=http://%s\n' % subscription_distro_url)
            rfo.write('enabled=1\n')
            rfo.write('gpgcheck=1\n')
            rfo.write('gpgkey=file://%sconf/ROCKSTOR-GPG-KEY\n'
                      % settings.ROOT_DIR)
            rfo.write('metadata_expire=1h\n')
        # Set file to rw- --- --- (600) via stat constants.
        os.chmod(yum_file, stat.S_IRUSR | stat.S_IWUSR)
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
    if date is None:
        # None date signifies no rpm installed so list all changelog entries.
        date = 'all'
    log = False
    available = False
    new_version = None
    updates = []
    try:
        o, e, rc = run_command([YUM, 'changelog', date, pkg])
    except CommandException as e:
        # Catch as yet unconfigured repos ie Leap 15.1: error log accordingly.
        # Avoids breaking current version display and update channel selection.
        emsg = 'Error\\: Cannot retrieve repository metadata \\(repomd.xml\\)'
        if re.match(emsg, e.err[-2]) is not None:
            logger.error('Rockstor repo for distro.id ({}) version ({}) may '
                         'not exist: pending or deprecated.\nReceived: ({}).'
                         .format(distro.id(), distro.version(), e.err))
            new_version = version  # Explicitly set (flag) for code clarity.
            return version, new_version, updates
        # otherwise we raise an exception as normal.
        raise e
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
            updates.append(l)
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

    return version, new_version, updates


def update_run(subscription=None, yum_update=False):
    # update_run modified to handle yum updates too
    # and avoid an ad hoc yum update function
    # If we have a yum update we don't stop/start Rockstor and
    # don't delete *.pyc files
    if (subscription is not None):
        switch_repo(subscription)

    run_command([SYSTEMCTL, 'start', 'atd'])
    fh, npath = mkstemp()
    with open(npath, 'w') as atfo:
        if not yum_update:
            atfo.write('%s stop rockstor\n' % SYSTEMCTL)
            # rockstor-pre stop ensures initrock re-run on next rockstor start
            atfo.write('%s stop rockstor-pre\n' % SYSTEMCTL)
            atfo.write('/usr/bin/find %s -name "*.pyc" -type f -delete\n'
                       % settings.ROOT_DIR)
            atfo.write('%s --setopt=timeout=600 -y update\n' % YUM)
            # account for moving from dev/source to package install:
            atfo.write('%s --setopt=timeout=600 -y install rockstor\n' % YUM)
            # the following rockstor start invokes rockstor-pre (initrock) also
            atfo.write('%s start rockstor\n' % SYSTEMCTL)
        else:
            atfo.write('%s --setopt=timeout=600 -y -x rock* update\n' % YUM)
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
    package_info['description'] = ''
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

    package_info['installed'] = '[line]'.join(package_info['installed'])
    package_info['available'] = '[line]'.join(package_info['available'])
    package_info['description'] = pkg_infos(package_info['name'],
                                            'DESCRIPTION')

    return package_info


def pkg_infos(package, tag="DESCRIPTION"):
    # Retrieve a package description and other infos  with some 'magic spells'
    # We query rpm dbs passing a queryformat, with default to DESCRIPTION
    # To @schakrava: this probably can help avoiding some reading loops used
    # to grab packages infos like on Rockstor updates check
    # Full ref for avail tags here: http://rpm.org/user_doc/query_format.html
    # and avail tags list with rpm --querytags
    tag = '%%{%s}' % tag
    out, err, rc = run_command([RPM, '-q', '--queryformat', tag, package],
                               throw=False)
    if (rc != 0):
        return ''

    return ' '.join(out)


def yum_check():
    # Query yum for updates and grab return code
    # yum check-update retun code is 0 with no updates
    # and 100 if at least 1 update available
    # Using -x rockstor* to avoid having Rockstor updated here
    # instead of Rockstor "ad hoc" updater
    out, err, rc = run_command([YUM, 'check-update', '-q', '-x', 'rock*'],
                               throw=False)
    packages = []
    # Read check-update output skipping first and last empty line
    # on every round we apply some beautify with pkg_changelog
    for line in out[1:-1]:
        packages.append(pkg_changelog(line.split()[0].strip()))

    return rc, packages
