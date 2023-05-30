"""
Copyright (c) 2012-2020 RockStor, Inc. <https://rockstor.com>
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
import re
from tempfile import mkstemp
from shutil import move
import logging
from system.osi import run_command, root_disk

SYSCTL_CONF = "/etc/sysctl.d/99-rockstor.conf"
ROOT_FS = [
    "/",
]


def is_flash(disk):
    flash = False
    o, e, rc = run_command(["udevadm", "info", "--name", disk])
    for line in o:
        if re.search("ID_BUS=", line) is not None:
            if line.strip().split()[1].split("=")[1] != "usb":
                logging.debug(
                    "drive({}) is not on usb bus. info: {}".format(disk, line)
                )
                flash = flash and False
        if re.search("ID_USB_DRIVER=usb-storage", line) is not None:
            logging.debug("usb-storage driver confirmed for {}".format(disk))
            flash = flash or True
    logging.info("usb flash drive validation from udevadm: {}".format(flash))
    # /sys/block/disk/queue/rotational is not reliable, but if [deadline] is in
    # /sys/block/disk/queue/scheduler, it's fair to assume flash
    logging.debug("Checking if scheduler is set to [deadline] for {}".format(disk))
    disk = disk.split("/")[-1]  # strip off the path
    # Note that the following may fail for sys on luks dev.
    with open("/sys/block/{}/queue/scheduler".format(disk)) as sfo:
        for line in sfo.readlines():
            if re.search("\[deadline\]", line) is not None:
                logging.debug("scheduler: {}".format(line))
                flash = flash and True
            else:
                flash = flash or False
                logging.debug("scheduler is not flash friendly. info: {}".format(line))
    logging.info("flashiness of the drive({}): {}".format(disk, flash))
    return flash


def update_sysctl():
    logging.debug("updating {}".format(SYSCTL_CONF))
    tuneups = [
        "vm.swappiness = 1",
        "vm.vfs_cache_pressure = 50",
        "vm.dirty_writeback_centisecs = 12000",
        "vm.dirty_expire_centisecs = 12000",
        "vm.dirty_ratio = 20",
        "vm.dirty_background_ratio = 1",
    ]
    fo, npath = mkstemp()
    with open(SYSCTL_CONF) as sfo, open(npath, "w") as tfo:
        for line in sfo.readlines():
            tfo.write(line)
            if line.strip() in tuneups:
                tuneups.remove(line.strip())
        for t in tuneups:
            tfo.write("{}\n".format(t))
    move(npath, SYSCTL_CONF)
    logging.info("moved {} to {}".format(npath, SYSCTL_CONF))
    o, e, rc = run_command(["/usr/sbin/sysctl", "-p"])
    logging.info("Successfully updated sysctl")
    logging.debug("sysctl -p out: {} err: {}".format(o, e))


def update_fstab():
    logging.debug("updating fstab with noatime")
    fo, npath = mkstemp()
    FSTAB = "/etc/fstab"
    with open(FSTAB) as ffo, open(npath, "w") as tfo:
        for line in ffo.readlines():
            if re.match("UUID=", line) is not None:
                fields = line.strip().split()
                if fields[1] in ROOT_FS:
                    if re.search("noatime", fields[3]) is not None:
                        tfo.write(line)
                    else:
                        fields[3] = "{},noatime".format(fields[3])
                        fields[4] = "{} {}\n".format(fields[4], fields[5])
                        fields.pop()
                        tfo.write("\t".join(fields))
                else:
                    tfo.write(line)
            else:
                tfo.write(line)
    move(npath, FSTAB)
    logging.info("moved {} to {}".format(npath, FSTAB))


def main():
    loglevel = logging.INFO
    if len(sys.argv) > 1 and sys.argv[1] == "-x":
        loglevel = logging.DEBUG
    logging.basicConfig(format="%(asctime)s: %(message)s", level=loglevel)
    rd = root_disk()
    logging.debug("Root drive is {}".format(rd))

    if is_flash(rd):
        update_sysctl()
        logging.info("updated sysctl")
        # emable tmpfs on /tmp
        # TODO: Requires modification for openSUSE, i.e. removing fstab entry:
        # https://en.opensuse.org/openSUSE:Tmp_on_tmpfs#openSUSE_Leap
        # In future Leap /tmp on tmpfs will be default. Already is in Tumbleweed.
        # tmpmnt = "tmp.mount"
        # systemctl(tmpmnt, "enable")
        # logging.info("enabled {}".format(tmpmnt))
        # systemctl(tmpmnt, "start")
        # logging.info("started {}".format(tmpmnt))

        # mount stuff with noatime
        # add noatime to /, /home and /boot in /etc/fstab
        update_fstab()
        logging.info("updated fstab re noatime")
        for fs in ROOT_FS:
            run_command(["mount", fs, "-o", "remount"])
            logging.info("remounted {}".format(fs))


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
