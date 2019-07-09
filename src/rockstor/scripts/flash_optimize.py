"""
Copyright (c) 2012-2015 RockStor, Inc. <http://rockstor.com>
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
import os
import re
from tempfile import mkstemp
from shutil import move
import logging
from system.osi import run_command, root_disk
from system.services import systemctl

HDPARM = '/usr/sbin/hdparm'
YUM = '/usr/bin/yum'
SYSTEMD_DIR = '/etc/systemd/system/'
FSTRIM_NAME = 'rockstor-fstrim'
FSTRIM_BASE = '%s%s' % (SYSTEMD_DIR, FSTRIM_NAME)
FSTRIM_SERVICE = '%s.service' % FSTRIM_BASE
FSTRIM_TIMER = '%s.timer' % FSTRIM_BASE
SYSCTL_CONF = '/etc/sysctl.d/99-rockstor.conf'
ROOT_FS = ['/', '/boot', '/home', ]


def fstrim_systemd():
    logging.debug('Setting up fstrim timer to run weekly once')
    with open(FSTRIM_SERVICE, 'w') as sfo:
        sfo.write('[Unit]\n')
        sfo.write('Description=Discard unused blocks\n\n')
        sfo.write('[Service]\n')
        sfo.write('Type=oneshot\n')
        sfo.write('ExecStart=/usr/sbin/fstrim -v /\n')
        sfo.write('ExecStart=/usr/sbin/fstrim -v /boot \n')
    logging.debug('Created %s' % FSTRIM_SERVICE)

    with open(FSTRIM_TIMER, 'w') as sto:
        sto.write('[Unit]\n')
        sto.write('Description=Discard unused blocks once a week\n')
        sto.write('Documentation=man:fstrim\n\n')
        sto.write('[Timer]\n')
        sto.write('OnCalendar=weekly\n')
        sto.write('AccuracySec=1h\n')
        sto.write('Persistent=true\n\n')
        sto.write('[Install]\n')
        sto.write('WantedBy=multi-user.target\n')
    logging.debug('Created %s' % FSTRIM_TIMER)

    systemctl(FSTRIM_NAME, 'enable')
    logging.info('Enabled %s' % FSTRIM_NAME)


def trim_support(disk):
    # 1. trim support.
    # verify if TRIM is supported
    # pre req: yum install hdparm
    logging.debug('Checking for TRIM support on %s' % disk)
    if (not os.path.exists(HDPARM)):
        logging.debug('hdparm not found. Installing')
        run_command([YUM, 'install', '-y', 'hdparm'])
        logging.info('Installed hdparm successfully')

    o, e, rc = run_command(['hdparm', '-I', '{}'.format(disk)])
    for l in o:
        if (re.search('Data Set Management TRIM supported', l) is not None):
            logging.debug('TRIM supported. info: %s' % l)
            return True
    logging.info('TRIM not supported on %s' % disk)
    return False


def is_flash(disk):
    flash = False
    o, e, rc = run_command(['udevadm', 'info', '--name', disk])
    for l in o:
        if (re.search('ID_BUS=', l) is not None):
            if (l.strip().split()[1].split('=')[1] != 'usb'):
                logging.debug('drive(%s) is not on usb bus. info: %s'
                              % (disk, l))
                flash = flash and False
        if (re.search('ID_USB_DRIVER=usb-storage', l) is not None):
            logging.debug('usb-storage driver confirmed for %s' % disk)
            flash = flash or True
    logging.info('usb flash drive validation from udevadm: %s' % flash)
    # /sys/block/disk/queue/rotational is not reliable, but if [deadline] is in
    # /sys/block/disk/queue/scheduler, it's fair to assume flash
    logging.debug('Checking if scheduler is set to [deadline] for %s' % disk)
    disk = disk.split('/')[-1]  # strip off the path
    # Note that the following may fail for sys on luks dev.
    with open('/sys/block/%s/queue/scheduler' % disk) as sfo:
        for l in sfo.readlines():
            if (re.search('\[deadline\]', l) is not None):
                logging.debug('scheduler: %s' % l)
                flash = flash and True
            else:
                flash = flash or False
                logging.debug('scheduler is not flash friendly. info: %s' % l)
    logging.info('flashiness of the drive(%s): %s' % (disk, flash))
    return flash


def update_sysctl():
    logging.debug('updating %s' % SYSCTL_CONF)
    tuneups = ['vm.swappiness = 1',
               'vm.vfs_cache_pressure = 50',
               'vm.dirty_writeback_centisecs = 12000',
               'vm.dirty_expire_centisecs = 12000',
               'vm.dirty_ratio = 20',
               'vm.dirty_background_ratio = 1', ]
    fo, npath = mkstemp()
    with open(SYSCTL_CONF) as sfo, open(npath, 'w') as tfo:
        for line in sfo.readlines():
            tfo.write(line)
            if (line.strip() in tuneups):
                tuneups.remove(line.strip())
        for t in tuneups:
            tfo.write('%s\n' % t)
    move(npath, SYSCTL_CONF)
    logging.info('moved {} to {}'.format(npath, SYSCTL_CONF))
    o, e, rc = run_command(['/usr/sbin/sysctl', '-p'])
    logging.info('Successfully updated sysctl')
    logging.debug('sysctl -p out: {} err: {}'.format(o, e))


def update_fstab():
    logging.debug('updating fstab with noatime')
    fo, npath = mkstemp()
    FSTAB = '/etc/fstab'
    with open(FSTAB) as ffo, open(npath, 'w') as tfo:
        for l in ffo.readlines():
            if (re.match('UUID=', l) is not None):
                fields = l.strip().split()
                if (fields[1] in ROOT_FS):
                    if (re.search('noatime', fields[3]) is not None):
                        tfo.write(l)
                    else:
                        fields[3] = '%s,noatime' % fields[3]
                        fields[4] = '%s %s\n' % (fields[4], fields[5])
                        fields.pop()
                        tfo.write('\t'.join(fields))
                else:
                    tfo.write(l)
            else:
                tfo.write(l)
    move(npath, FSTAB)
    logging.info('moved %s to %s' % (npath, FSTAB))


def main():
    loglevel = logging.INFO
    if (len(sys.argv) > 1 and sys.argv[1] == '-x'):
        loglevel = logging.DEBUG
    logging.basicConfig(format='%(asctime)s: %(message)s', level=loglevel)
    rd = root_disk()
    logging.debug('Root drive is %s' % rd)
    do_more = False
    if (trim_support(rd) is True):
        do_more = True
        logging.info('TRIM support is available for %s' % rd)
        fstrim_systemd()
        logging.debug('Finished setting up fstrim timer')
    do_more = do_more or is_flash(rd)

    if (do_more):
        update_sysctl()
        logging.info('updated sysctl')
        # emable tmpfs on /tmp
        tmpmnt = 'tmp.mount'
        systemctl(tmpmnt, 'enable')
        logging.info('enabled %s' % tmpmnt)
        systemctl(tmpmnt, 'start')
        logging.info('started %s' % tmpmnt)

        # mount stuff with noatime
        # add noatime to /, /home and /boot in /etc/fstab
        update_fstab()
        logging.info('updated fstab')
        for fs in ROOT_FS:
            run_command(['mount', fs, '-o', 'remount'])
            logging.info('remounted %s' % fs)


# change the I/O scheduler to noop or deadline.  turns out this is not
# necessary. deadline scheduler is default for non sata drives in Centos/Redhat
# 7 run_command(['echo', 'deadline', '>', '/sys/block/%s/queue/scheduler' %
# root_disk])

# add deadline scheduler to kernel parameters this is also not necessary since
# deadline scheduler is default for non sata drives.  in /etc/grub/default
# GRUB_CMDLINE_LINUX="crashkernel=auto rhgb quiet elevator=deadline"
# run_command(['grub2-mkconfig', '-o', '/boot/grub2/grub.cfg'])

# useful links
# https://wiki.archlinux.org/index.php/Solid_State_Drives
# http://blog.neutrino.es/2013/howto-properly-activate-trim-for-your-ssd-on-linux-fstrim-lvm-and-dmcrypt/
# http://www.certdepot.net/rhel7-extend-life-ssd/
# https://gist.github.com/ngnpope/3806732
# http://www.cyrius.com/debian/nslu2/linux-on-flash/
# http://www.storagesearch.com/ssd.html
# http://superuser.com/questions/228657/which-linux-filesystem-works-best-with-ssd#answer-550308
# http://lists.freedesktop.org/archives/systemd-devel/2015-March/029842.html
