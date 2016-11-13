#!/bin/bash
#
# Simple shell script to dump the raw smartctl command output as used internally
# by Rockstor prior to parsing for Web-UI accessible SMART info.
#
# Intended as an aid to reporting SMART parsing issues on:
# https://forum.rockstor.com/
#

# Check number of script arguments.
if [ "$#" -ne 1 ]; then
    echo
    echo "Please supply a single device name using the /dev/sdX or /dev/disk/by-id reference"
    echo "N.B. Use the base device - not a partition reference."
    echo "eg $0 /dev/disk/by-id/ata-ST3160021AS_5JS1HNX9"
    echo
    exit
fi

DEVNAME=$1

# Our smartctl dump generator
dump_smartctl_outputs () {
    echo "creating our working directory or \"/root/smartdumps\""
    mkdir -p /root/smartdumps
    echo "dumping output of \"smartctl -a $DEVNAME\" to /root/smartdumps/smart-a.out"
    /usr/sbin/smartctl -a $DEVNAME > /root/smartdumps/smart-a.out
    echo "dumping output of \"smartctl -c $DEVNAME\" to /root/smartdumps/smart-c.out"
    /usr/sbin/smartctl -c $DEVNAME > /root/smartdumps/smart-c.out
    echo "dumping output of \"smartctl -l error $DEVNAME\" to /root/smartdumps/smart-l-error.out"
    /usr/sbin/smartctl -l error $DEVNAME > /root/smartdumps/smart-l-error.out
    echo "dumping output of \"smartctl -l selftest -l selective $DEVNAME\" to /root/smartdumps/smart-l-selftest-l-selective.out"
    /usr/sbin/smartctl -l selftest -l selective $DEVNAME > /root/smartdumps/smart-l-selftest-l-selective.out
    echo "dumping output of \"smartctl --info $DEVNAME\" to /root/smartdumps/smart--info.out"
    /usr/sbin/smartctl --info $DEVNAME > /root/smartdumps/smart--info.out
    echo "dumping output of \"smartctl -H --info $DEVNAME\" to /root/smartdumps/smart-H--info.out"
    /usr/sbin/smartctl -H --info $DEVNAME > /root/smartdumps/smart-H--info.out
    echo "dumping output of lsblk to /root/smartdumps/lsblk.out"
    /usr/bin/lsblk > /root/smartdumps/lsblk.out
    echo "zipping all /root/smartdumps/*.out files"
    tar czf /root/smart-issue-report.tar.gz /root/smartdumps/*.out
}

# Check if first parameter is a block device
if [ -b "$1" ]; then
    echo "Generating /root/smart-issue-report.tar.gz"
    dump_smartctl_outputs
    echo "Please supply the generated \"/root/smart-issue-report.tar.gz\" file in connection with your SMART parsing issue"
else
    echo "Sorry this does not appear to be a block device."
    echo "Please supply a valid smartctl block device."
fi

