"""
Copyright (c) 2012-2019 RockStor, Inc. <http://rockstor.com>
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

import logging
import re
from shutil import move
from tempfile import mkstemp

import distro

from exceptions import CommandException
from osi import run_command, get_base_device_byid, get_device_path
from system.email_util import email_root

logger = logging.getLogger(__name__)

SMART = "/usr/sbin/smartctl"
CAT = "/usr/bin/cat"
# enables reading file dumps of smartctl output instead of running smartctl
# currently hardwired to read from eg:- /root/smartdumps/smart-H--info.out
# default setting = False
TESTMODE = False


def info(device, custom_options="", test_mode=TESTMODE):
    """
    Retrieve matching properties found in smartctl -H --info output.
    Used to populate the Identity / general info tab by views/disk_smart.py
    :param device: disk device name
    :param test_mode: False causes cat from file rather than smartctl command
    :return: list of smart parameters extracted from device or test file
    """
    if not test_mode:
        o, e, rc = run_command(
            [SMART, "-H", "--info"] + get_dev_options(device, custom_options),
            throw=False,
        )
    else:  # we are testing so use a smartctl -H --info file dump instead
        o, e, rc = run_command([CAT, "/root/smartdumps/smart-H--info.out"])
    # List of string matches to look for in smartctrl -H --info output.
    # Note the "|" char allows for defining alternative matches ie A or B
    matches = (
        "Model Family:|Vendor:",
        "Device Model:|Product:",
        "Serial Number:|Serial number:",
        "LU WWN Device Id:|Logical Unit id:",
        "Firmware Version:|Revision",
        "User Capacity:",
        "Sector Sizes?:|Logical block size:",
        "Rotation Rate:",
        "Device is:",
        "ATA Version is:",
        "SATA Version is:",
        "Local Time is:",
        "SMART support is:.* Available",
        "SMART support is:.* Enabled",
        "SMART overall-health self-assessment|SMART Health Status:",
    )
    # create a list of empty strings ready to store our smart results / values
    res = [""] * len(matches)
    version = ""
    for line in o:
        if re.match("smartctl ", line) is not None:
            version = " ".join(line.split()[1:4])
        for i in range(len(matches)):
            if re.match(matches[i], line) is not None:
                # find location of first colon
                first_colon = re.search(":", line).start()
                # Assume all characters after colon are the result / value and
                # strip off begin and end spaces. Limit to 64 chars for db.
                res[i] = line[first_colon + 1 :].strip()[:64]
    # smartctl version is expected at index 14 (15th item)
    res.insert(14, version)
    return res


def extended_info(device, custom_options="", test_mode=TESTMODE):
    """Retrieves a list of SMART attributes found from parsing smartctl -a output
    Mostly ATA / SATA as SCSI uses a free form syntax for this.  Extracts all
    lines starting with ID# ATTRIBUTE_NAME and creates a dictionary of lists
    containing each lines column entries indexed in the dictionary via the
    Attribute name.

    :param device: disk device name
    :param testmode: Not True causes cat from file rather than smartctl command
    :return: dictionary of smart attributes extracted from device or test file

    """
    if not test_mode:
        o, e, rc = run_command(
            [SMART, "-a"] + get_dev_options(device, custom_options), throw=False
        )
    else:  # we are testing so use a smartctl -a file dump instead
        o, e, rc = run_command([CAT, "/root/smartdumps/smart-a.out"])
    attributes = {}
    for i in range(len(o)):
        if (
            re.match("Vendor Specific SMART Attributes with Thresholds:", o[i])
            is not None
        ):
            if len(o) > i + 1:
                if re.match("ID# ATTRIBUTE_NAME", o[i + 1]) is not None:
                    for j in range(i + 2, len(o)):
                        if o[j] == "":
                            break
                        fields = o[j].strip().split()
                        if len(fields) > 10:
                            fields[9] = " ".join(fields[9:])
                        # Some drives return "---" as a Threshold value, in
                        # this case substitute 999 as an integer equivalent.
                        if fields[5] == "---":
                            fields[5] = "999"
                        attributes[fields[1]] = fields[0:10]
    return attributes


def capabilities(device, custom_options="", test_mode=TESTMODE):
    """Retrieves a list of SMART capabilities found from parsing smartctl -c
    output ATA / SATA only.  Extracts all capabilities and build a dictionary
    of lists containing ID, Name, Flag, and description for each capability
    found. The dictionary is indexed by the capability name.

    :param device:    disk device name
    :param test_mode: False causes cat from file rather than smartctl command
    :return:          dictionary of smart capabilities extracted from device
                      or test file
    """
    if not test_mode:
        o, e, rc = run_command([SMART, "-c"] + get_dev_options(device, custom_options))
    else:  # we are testing so use a smartctl -c file dump instead
        o, e, rc = run_command([CAT, "/root/smartdumps/smart-c.out"])
    cap_d = {}
    for i in range(len(o)):
        if re.match("=== START OF READ SMART DATA SECTION ===", o[i]) is not None:
            prev_line = None
            cur_cap = None
            for j in range(i + 2, len(o)):
                if re.match(".*:\s+\(.*\)", o[j]) is not None:
                    cap = o[j][: o[j].index(":")]
                    flag = o[j][(o[j].index("(") + 1) : o[j].index(")")].strip()
                    val = o[j][(o[j].index(")") + 1) :].strip()
                    if val == "seconds." or val == "minutes.":
                        val = "%s %s" % (flag, val)
                        flag = ""
                    if prev_line is not None:
                        cap = "%s %s" % (prev_line, cap)
                        prev_line = None
                    cur_cap = cap
                    cap_d[cur_cap] = [flag, val]
                elif re.match("\s", o[j]) is not None:
                    cap_d[cur_cap][1] += "\n"
                    cap_d[cur_cap][1] += o[j].strip()
                else:
                    prev_line = o[j].strip()
            break
    return cap_d


def error_logs(device, custom_options="", test_mode=TESTMODE):
    """Retrieves a parsed list of SMART errors from the output of smartctl -l
    error May be empty if no errors, also returns a raw output of the error log
    itself

    :param device:    disk device name
    :param test_mode: False causes cat from file rather than smartctl command
    :return: summary: dictionary of lists containing details of error. Index is
                      error number.
    :return: log_l:   A list containing each line in turn of the error log.
    """
    local_base_dev = get_dev_options(device, custom_options)
    smart_command = [SMART, "-l", "error"] + local_base_dev
    if not test_mode:
        o, e, rc = run_command(smart_command, throw=False)
    else:
        o, e, rc = run_command([CAT, "/root/smartdumps/smart-l-error.out"])
    # As we mute exceptions when calling the above command we should at least
    # examine what we have as return code (rc); 64 has been seen when the error
    # log contains errors but otherwise executes successfully so we catch this.
    overide_rc = 64
    e_msg = (
        "Drive %s has logged S.M.A.R.T errors. Please view "
        "the Error logs tab for this device." % local_base_dev
    )
    screen_return_codes(e_msg, overide_rc, o, e, rc, smart_command)
    ecode_map = {
        "ABRT": "Command ABoRTed",
        "AMNF": "Address Mark Not Found",
        "CCTO": "Command Completion Timed Out",
        "EOM": "End Of Media",
        "ICRC": "Interface Cyclic Redundancy Code (CRC) error",
        "IDNF": "IDentity Not Found",
        "ILI": "(packet command-set specific)",
        "MC": "Media Changed",
        "MCR": "Media Change Request",
        "NM": "No Media",
        "obs": "obsolete",
        "TK0NF": "TracK 0 Not Found",
        "UNC": "UNCorrectable Error in Data",
        "WP": "Media is Write Protected",
    }
    summary = {}
    log_l = []
    for i in range(len(o)):
        if re.match("=== START OF READ SMART DATA SECTION ===", o[i]) is not None:
            err_num = None
            lifetime_hours = None
            state = None
            etype = None
            details = None
            for j in range(i + 1, len(o)):
                log_l.append(o[j])
                if re.match("Error ", o[j]) is not None:
                    fields = o[j].split()
                    err_num = fields[1]
                    if "lifetime:" in fields:
                        lifetime_hours = int(fields[fields.index("lifetime:") + 1])
                if (
                    re.match(
                        "When the command that caused the error occurred,"
                        " the device was",
                        o[j].strip(),
                    )
                    is not None
                ):
                    state = o[j].strip().split("the device was ")[1]
                if re.search("Error: ", o[j]) is not None:
                    e_substr = o[j].split("Error: ")[1]
                    e_fields = e_substr.split()
                    etype = e_fields[0]
                    if etype in ecode_map:
                        etype = ecode_map[etype]
                    details = (
                        " ".join(e_fields[1:])
                        if (len(e_fields) > 1)
                        else "No Sector Details Available"
                    )
                    summary[err_num] = list([lifetime_hours, state, etype, details])
                    err_num = lifetime_hours = state = etype = details = None
    return (summary, log_l)


def test_logs(device, custom_options="", test_mode=TESTMODE):
    """Retrieves information from SMART Self-Test logs held by the drive.  Creates
    a dictionary of previous test info, indexed by test number and a list
    containing the remaining log info, each line is an item in the list.

    :param device: disk device name
    :param test_mode: False causes cat from file rather than smartctl command
    :return: tuple of test_d as a dictionary of summarized test, plus a list
    """
    smart_command = [SMART, "-l", "selftest", "-l", "selective"] + get_dev_options(
        device, custom_options
    )
    if not test_mode:
        o, e, rc = run_command(smart_command, throw=False)
    else:
        o, e, rc = run_command(
            [CAT, "/root/smartdumps/smart-l-selftest-l-selective.out"]
        )
    # A return code of 128 (non zero so run_command raises an exception) has
    # been seen when executing this command. Strange as it means
    # "Invalid argument to exit" anyway if we silence the throw of a generic
    # non 0 exception we can catch the 128, akin to 64 catch in error_logs().
    # N.B. no official list of rc = 128 in /usr/include/sysexits.h
    overide_rc = 128
    e_msg = (
        "run_command(%s) returned an error of %s. This has undetermined "
        "meaning. Please view the Self-Test Logs tab for this device."
        % (smart_command, overide_rc)
    )
    screen_return_codes(e_msg, overide_rc, o, e, rc, smart_command)
    test_d = {}
    log_l = []
    for i in range(len(o)):
        if re.match("SMART Self-test log structure revision number", o[i]) is not None:
            log_l.append(o[i])
            if len(o) > (i + 1):
                if re.match("Num  Test_Description    Status", o[i + 1]) is not None:
                    for j in range(i + 2, len(o)):
                        if re.match("# ", o[j]) is not None:
                            # slit the line into fields using 2 or more spaces
                            fields = re.split(r"\s\s+", o[j].strip()[2:])
                            # Some Seagate drives add an ongoing test progress
                            # report to the top of this log but there is then
                            # only one space delimiter and we loose a column.
                            if len(fields) == 5:  # it's normally 6 fields
                                # we are missing a column (fast check)
                                if re.match("Self-test routine in progress", fields[2]):
                                    # An ongoing self-test entry is to blame.
                                    status_fields = fields[2].split()
                                    # Move our last two line fields along one.
                                    fields.insert(5, fields[4])
                                    fields[4] = fields[3]
                                    # Move end of status field percentage to
                                    # freshly freed up column in line list.
                                    fields[3] = status_fields[-1]
                                    # Remove our % remaining in status field.
                                    fields[2] = " ".join(status_fields[:-1])
                            # Remove the % char from this columns value
                            # and change % Remaining to % Completed.
                            fields[3] = 100 - int(fields[3][:-1])
                            test_d[fields[0]] = fields[1:]
                        else:
                            log_l.append(o[j])
    return (test_d, log_l)


def run_test(device, test, custom_options=""):
    # start a smart test(short, long or conveyance)
    return run_command([SMART, "-t", test] + get_dev_options(device, custom_options))


def available(device, custom_options="", test_mode=TESTMODE):
    """
    Returns boolean pair: true if SMART support is available on the device and
    true if SMART support is enabled.
    Used by update_disk_state in views/disk.py to assess smart status
    :param device:
    :return: available (boolean), enabled (boolean)
    """
    if not test_mode:
        o, e, rc = run_command(
            [SMART, "--info"] + get_dev_options(device, custom_options)
        )
    else:  # we are testing so use a smartctl --info file dump instead
        o, e, rc = run_command([CAT, "/root/smartdumps/smart--info.out"])
    a = False
    e = False
    for i in o:
        # N.B. .* in pattern match to allow for multiple spaces
        if re.match("SMART support is:.* Available", i) is not None:
            a = True
        if re.match("SMART support is:.* Enabled", i) is not None:
            e = True
    return a, e


def toggle_smart(device, custom_options="", enable=False):
    switch = "on" if (enable) else "off"
    # enable SMART support of the device
    return run_command(
        [SMART, "--smart=%s" % switch] + get_dev_options(device, custom_options)
    )


def update_config(config):
    # The location of smartd.conf differs between openSUSE and CentOS.
    # For sustainability and simplicity, set openSUSE's location as default
    distro_id = distro.id()
    if distro_id == "rockstor":
        SMARTD_CONFIG = "/etc/smartmontools/smartd.conf"
    else:
        SMARTD_CONFIG = "/etc/smartd.conf"
    ROCKSTOR_HEADER = (
        "###BEGIN: Rockstor smartd config. DO NOT EDIT BELOW " "THIS LINE###"
    )
    fo, npath = mkstemp()
    with open(SMARTD_CONFIG) as sfo, open(npath, "w") as tfo:
        for line in sfo.readlines():
            if re.match("DEVICESCAN", line) is not None:
                # comment out this line, if not, smartd ignores everything else
                tfo.write("#%s" % line)
            elif re.match(ROCKSTOR_HEADER, line) is None:
                tfo.write(line)
            else:
                break
        tfo.write("%s\n" % ROCKSTOR_HEADER)
        for l in config.split("\n"):
            tfo.write("%s\n" % l)

    return move(npath, SMARTD_CONFIG)


def screen_return_codes(msg_on_hit, return_code_target, o, e, rc, command):
    """Provides a central mechanism to screen return codes from executing smart
    commands. This is required as some non zero return codes would otherwise
    trigger a generic exception clause in our general purpose run_command.  If
    the target return code is seen then email root with the message provided,
    otherwise raise a generic exception with the command information.  N.B. May
    be done better by acting as a SMART run_command wrapper (Future).

    :param msg_on_hit: message used to email root
    :param return_code_target: return code to screen for
    :param o: the output from the command when it was run
    :param e: the error from the command when it was run
    :param rc: the return code from running the command
    :param command: the command that produced the previous o, e, and rc params.

    """
    # if our return code is our target then log with our message and email root
    # with the same.
    if rc == return_code_target:
        logger.error(msg_on_hit)
        email_root("S.M.A.R.T error", msg_on_hit)
    # In all other non zero (error) instances we raise an exception as normal.
    elif rc != 0:
        e_msg = "non-zero code(%d) returned by command: %s output: " "%s error: %s" % (
            rc,
            command,
            o,
            e,
        )
        logger.error(e_msg)
        raise CommandException(("%s" % command), o, e, rc)


def get_dev_options(dev_byid, custom_options=""):
    """Returns device specific options for all smartctl commands.  Note that in
    most cases this requires looking up the base device via get_base_device but
    in some instances this is not required as in the case of devices behind
    some raid controllers. If custom_options contains known raid controller
    smartctl targets then these will be substituted for device name.

    :param dev_byid:  device name as per db entry, ie by-id type without a path
    :param custom_options: string of user entered custom smart options.
    :return: dev_options: list containing the device specific smart options and
    the appropriate smart device target with full path.

    """
    # Initially our custom_options parameter may be None, ie db default prior
    # to any changes having been made. Deal with this by adding a guard.
    if custom_options is None or custom_options == "":
        # Empty custom_options or they have never been set so just return
        # full path to base device as nothing else to do.
        dev_options = [get_device_path(get_base_device_byid(dev_byid, TESTMODE))]
    else:
        # Convert string of custom options into a list ready for run_command
        # TODO: think this ascii should be utf-8 as that's kernel standard
        # TODO: or just use str(custom_options).split()
        dev_options = custom_options.encode("ascii").split()
        # Remove Rockstor native 'autodev' custom smart option raid dev target.
        # As we automatically add the full path by-id if a raid controller
        # target dev is not found, we can simply remove this option.
        # N.B. here we assume there is either 'autodev' or a specified target:
        # input validation was tested to reject both being entered.
        if "autodev" in dev_options:
            dev_options.remove("autodev")
        # If our custom options don't contain a raid controller target then add
        # the full path to our base device as our last device specific option.
        if re.search("/dev/tw|/dev/cciss/c|/dev/sg|/dev/sd", custom_options) is None:
            # add full path to our custom options as we see no raid target dev
            dev_options += [get_device_path(get_base_device_byid(dev_byid, TESTMODE))]
    # Note on raid controller target devices.  /dev/twe#, or /dev/twa#, or
    # /dev/twl# are 3ware controller targets devs respectively 3x-xxxx,
    # 3w-9xxx, and t2-sas (3ware/LSI 9750) drivers for respectively 6000, 7000,
    # 8000 or 9000 or 3ware/LSI 9750 controllers.  /dev/cciss/c0d0 is the first
    # HP/Compaq Smart Array Controller using the deprecated cciss driver
    # /dev/sg0 is the first hpsa or hpahcisr driver device for the same
    # adapter.  This same target device is also used by the Areca SATA RAID
    # controller except that the first device is /dev/sg2.
    return dev_options
