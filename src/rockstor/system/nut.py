"""
Copyright (c) 2012-2014 Rockstor, Inc. <http://rockstor.com>
This file is part of Rockstor.

Rockstor is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

Rockstor is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

# todo revise comments for brevity

# for CentOS nut systemd files are:-
# from nut package
# /usr/lib/systemd/system/nut-driver.service
# /usr/lib/systemd/system/nut-server.service
# N.B. the Type=simple so just a process start
# the nut-server requires the nut-driver and is started before:-
# from nut-client package
# /usr/lib/systemd/system/nut-monitor.service
# /lib/systemd/system-shutdown/nutshutdown
# note nut-monitor.service is set to start after nut-server.service

# N.B. some config options passed to nut from service configuration are used
# in multiple configuration files ie upsname in ups.conf and upsmon.conf

# N.B. if this config arrangement fails to prove robust then re-write using
# http://augeas.net/ configuration API and use python-augeas package
# and augeas and augeas-libs and lensens from nut source "nut/scripts/augeas"

import re
import collections
from tempfile import mkstemp
from shutil import move
from copy import deepcopy

import logging
from django.conf import settings
import shutil
from system.osi import run_command

logger = logging.getLogger(__name__)

CHMOD = '/usr/bin/chmod'
CHOWN = '/usr/bin/chown'

# NUT scheduler files for dealing with event / notices / action.
# Directories as per default CentOS install to maintain SELinux compatibility.
UPSSCHED = '/usr/sbin/upssched'
UPSSCHED_CONF = '/etc/ups/upssched.conf'
UPSSCHED_CMD = '/usr/bin/upssched-cmd'

# CONSTANTS of file names and associated tuples (immutable lists) of accepted
# / known options in those config files
# These might be better as collections.namedtuples
NUT_CONFIG = '/etc/ups/nut.conf'
NUT_CONFIG_OPTIONS = ("MODE")
NUT_UPS_CONFIG = '/etc/ups/ups.conf'
NUT_UPS_CONFIG_OPTIONS = ("upsname", "driver", "port", "cable", "serial",
                          "desc", "community")
NUT_UPSD_CONFIG = '/etc/ups/upsd.conf'
NUT_UPSD_CONFIG_OPTIONS = ("LISTEN", "MAXAGE")
NUT_USERS_CONFIG = '/etc/ups/upsd.users'
NUT_USERS_CONFIG_OPTIONS = ("nutuser", "password", "upsmon")
NUT_MONITOR_CONFIG = '/etc/ups/upsmon.conf'
# The following options are used in pre-processing to create the MONITOR line
# for upsmon.conf ("upsname", "nutserver", "nutuser", "password" "upsmon")
NUT_MONITOR_CONFIG_OPTIONS = ("NOTIFYCMD", "POLLFREQ", "MONITOR", "DEADTIME",
                              "SHUTDOWNCMD", "NOTIFYFLAG ONLINE",
                              "NOTIFYFLAG ONBATT", "NOTIFYFLAG LOWBATT",
                              "NOTIFYFLAG FSD", "NOTIFYFLAG COMMOK",
                              "NOTIFYFLAG COMMBAD",
                              "NOTIFYFLAG SHUTDOWN", "NOTIFYFLAG REPLBATT",
                              "NOTIFYFLAG NOCOMM", "NOTIFYFLAG NOPARENT")

# The events that will trigger a notify action.
NOTIFY_EVENTS = ("ONLINE", "ONBATT", "LOWBATT", "FSD", "COMMOK", "COMMBAD",
                 "SHUTDOWN", "REPLBATT", "NOCOMM", "NOPARENT")

# A catch all list: we always remark out lines containing the following words:
# (hack to work around only having whole word removal methods in our parser.)
REMARK_OUT = ("NOTIFYFLAG")

# Currently we only deal with upsmon  as master or slave in a single user
# entry and apply the same upsmon value to the end of the MONITOR line in
# upsmon.conf

# a dictionary for each config files associated known options.
nut_options_dict = {NUT_CONFIG: NUT_CONFIG_OPTIONS,
                    NUT_UPS_CONFIG: NUT_UPS_CONFIG_OPTIONS,
                    NUT_UPSD_CONFIG: NUT_UPSD_CONFIG_OPTIONS,
                    NUT_USERS_CONFIG: NUT_USERS_CONFIG_OPTIONS,
                    NUT_MONITOR_CONFIG: NUT_MONITOR_CONFIG_OPTIONS}

# a dictionary to identify what options are section headers in what files
nut_section_heads = {"upsname": NUT_UPS_CONFIG, "nutuser": NUT_USERS_CONFIG}

# dictionary of delimiters used, if not in this dict then "=" is assumed
nut_option_delimiter = {"LISTEN": " ", "MAXAGE": " ",
                        "MINSUPPLIES": " ", "upsmon": " ", "MONITOR": " ",
                        "POLLFREQ": " ", "DEADTIME": " ", "SHUTDOWNCMD": " ",
                        "NOTIFYCMD": " ", "NOTIFYFLAG ONLINE": " ",
                        "NOTIFYFLAG ONBATT": " ", "NOTIFYFLAG LOWBATT": " ",
                        "NOTIFYFLAG FSD": " ", "NOTIFYFLAG COMMOK": " ",
                        "NOTIFYFLAG COMMBAD": " ", "NOTIFYFLAG SHUTDOWN": " ",
                        "NOTIFYFLAG REPLBATT": " ", "NOTIFYFLAG NOCOMM": " ",
                        "NOTIFYFLAG NOPARENT": " "}


def config_upssched():
    """
    Overwite nut default upssched.conf and upssched-cmd files with Rockstor
    versions. Set owner.group and permissions to originals.
    """
    # the upssched config file
    upsshed_conf_template = ('%s/upssched.conf' % settings.CONFROOT)
    # would be better if we could set a file creation mask first then copy
    # todo set file creation mask to 640
    shutil.copyfile(upsshed_conf_template, UPSSCHED_CONF)
    run_command([CHOWN, 'root.nut', UPSSCHED_CONF])
    run_command([CHMOD, '640', UPSSCHED_CONF])
    # the upssched command file
    upsshed_cmd_template = ('%s/upssched-cmd' % settings.CONFROOT)
    shutil.copyfile(upsshed_cmd_template, UPSSCHED_CMD)
    run_command([CHOWN, 'root.root', UPSSCHED_CMD])
    # going with existing rights but this should be reviewed
    run_command([CHMOD, '755', UPSSCHED_CMD])


def establish_config_defaults(config):
    """
    Sanitizes input ie if empty config then throw an exception or set defaults.
    Also if no mode then choose "None" as we should never have no mode so
    there's a problem if we are not empty config but we have no mode!
    N.B. this works on the original config to sanitize what is saved in
    front end memory. Note that these sanitizing defaults must be consistent
    with storageadmin/static/storageadmin/js/views/configure_service.js
    """
    # An empty config dictionary will be false so raise exception as what else.
    if not config:
        # todo I am unsure if this is the best way to raise an exception here.
        e_msg = ('No NUT-UPS configuration found, make sure you have'
                 'configured this service properly.')
        raise Exception(e_msg)
    # if mode is present but empty then change to "none" as we should never
    # have empty mode so we can't know what it is supposed to be.
    if ('mode' in config) and (config['mode'] == ''):
        config['mode'] = 'none'
    # if upsname is not present or is present but empty then make it "ups"
    if (('upsname' in config) and (config['upsname'] == '')) or (
                'upsname' not in config):
        config['upsname'] = 'ups'
    if ('nutserver' in config) and (config['nutserver'] == ''):
        config['nutserver'] = 'localhost'


def configure_nut(config):
    """
    Top level nut config function. Takes the input config and initially applies
    any defaults that the front end failed to assert and then make a copy prior
    to sending to pre-processing and then in turn to final config application.
    Also establishes Rockstor defaults for upssched.
    :param config: sanitized config from input form
    :return:
    """
    # clean config and establish defaults
    establish_config_defaults(config)

    # As we change the config prior to its application in the config files we
    # must work on a deep copy to avoid breaking the front end 'memory'.
    # Note we could use a custom deepcopy to do some of our pre-processing
    # ie the re-writing of indexes and surrounding password and desc in ""
    config_copy = deepcopy(config)

    # Pre-process the config options so we know which files to put what options
    # in and in what order
    all_nut_configs = pre_process_nut_config(config_copy)
    # now go through each file - options pair and apply the config
    for config_file, config_options in all_nut_configs.items():
        # consider parallelizing these calls by executing on it's own thread
        # should be safe as "pleasingly parallel".
        update_config_in(config_file, config_options, REMARK_OUT,
                         settings.NUT_HEADER)
        # correct nut config file permissions from the default root rw -- --
        # without this nut services cannot access the details they require as
        # on startup nut mostly drops root privileges and runs as the nut user.
        # nut-client installs upsmon.conf and upssched.conf
        # ups.conf must be readable by upsdrvctl and any drivers and upsd
        # all nut config files by default in a CentOS install are 640 but our
        # file editing process creates a temp file and copies it over as root
        # the files as is are left as root.nut owner group so:-
        # os.chmod(config_file, 0644)
        run_command([CHMOD, '640', config_file])
    config_upssched()


def pre_process_nut_config(config):
    """
    Populates a dictionary of dictionaries where the top level dict is indexed
    by a config file path & name string, each top level entry (config file) is
    paired with an OrderedDict of options. This way we have:-
    "file -> options_in_order" pairs.
    OrderedDict allows for section head sub-sectin ordering eg:-
    [myups]
    driver = apcsmart
    port = /dev/ttyS1
    cable = 1234
    desc = "old-apc"
    from:-
    {'/etc/ups/ups.conf' : {'upsname': 'myups', 'driver': 'apcsmart', 'port':
    '/dev/ttyS1', 'cable': '1234', 'desc': 'old-apc'} }
    Problem:- how do we know what a section header is?
    Answer is the specific pre_processors know this about their service so can
    change eg 'upsname': 'myups' pair to 'section--upsname': 'myups' and only
    gain information as the key value is a section not an "option = value".
    The generic config file writer can then act on this 'tagging' of section
    headers accordingly: see update_config_in for implementation.
    :param config: sanitized config dict from form entry
    :return: dict of OrderedDicts indexed by file ie multiple entries of
    'file': {key: value, key:value}
    """
    # create local structure to populate:-
    # dictionary of items with:- {'path-to-file', {OrderedDict-of-options}}
    nut_configs = {NUT_CONFIG: collections.OrderedDict(),
                   NUT_UPS_CONFIG: collections.OrderedDict(),
                   NUT_UPSD_CONFIG: collections.OrderedDict(),
                   NUT_USERS_CONFIG: collections.OrderedDict(),
                   NUT_MONITOR_CONFIG: collections.OrderedDict()}

    # change mode index to uppercase as front end didn't like uppercase ref
    config['MODE'] = config.pop('mode')

    # wrap the value entries for password and desc in double inverted commas
    config['password'] = ('"%s"' % config['password'])
    config['desc'] = ('"%s"' % config['desc'])

    # set nut shutdown command wrapped in double inverted commas
    config['SHUTDOWNCMD'] = ('"%s"' % settings.NUT_SYSTEM_SHUTDOWNCMD)

    # set nut network LISTEN to LISTEN_ON_IP when in netserver mode, else ll.
    if config['MODE'] == 'netserver':
        config['LISTEN'] = settings.NUT_LISTEN_ON_IP
    else:
        config['LISTEN'] = 'localhost'

    # set the notify command to use NUT's built in scheduler
    # upsmon ---> calls nut's upssched ---> calls our CMDSCRIPT
    # see config_upssched()
    config['NOTIFYCMD'] = UPSSCHED

    # setup the response type for notifications ie NOTIFYFLAG <EVENT> <TYPE>
    # all events are listed in NOTIFY_EVENTS, types are SYSLOG WALL EXEC
    for event in NOTIFY_EVENTS:
        config[('NOTIFYFLAG ' + event)] = "SYSLOG+WALL+EXEC"

    # Create key value for MONITOR (upsmon.conf) line eg:-
    # "MONITOR": "upsname@nutserver 1 nutuser password master"
    nut_configs[NUT_MONITOR_CONFIG]['MONITOR'] = ('%s@%s 1 %s %s %s' % (
        config['upsname'], config['nutserver'], config['nutuser'],
        config['password'], config['upsmon']))
    logger.info(
        'NUT MONITOR LINE = %s' % nut_configs[NUT_MONITOR_CONFIG]['MONITOR'])

    # move section headings from config to nut_configs OrderedDicts
    # this way all following entries will pertain to them in their respective
    # config files. Assumes each section head is required in at most one file
    for section_header, config_file in nut_section_heads.items():
        if section_header in config:
            # we have found a config item that should be a section header so
            # pop it out from config and add it to the appropriate nut_configs.
            # This is where we can add the "section--" tag to this key.
            nut_configs[config_file][
                ('section--' + section_header)] = config.pop(section_header)
    # iterate over the nut_options_dict to allocate the configs to the
    # right section in nut_configs so they can be applied to the correct file.
    # N.B. we don't pop from config as some options are used in multiple files
    for config_file, file_options in nut_options_dict.items():
        # now repeatedly match config's entries to our host loops offerings.
        for config_option, config_value in config.items():
            if config_option in file_options:
                # add this config_option and value pair to our nut_configs
                nut_configs[config_file][config_option] = config_value
    return nut_configs


def update_config_in(config_file, config, remove_all, header):
    """
    # potentially upgrade this to a generic config writer via class def.
    Remark out all occurrences of options in config dict above HEADER.
    Apply key, value pairs in config dict as option = value setting in file
    after HEADER unless key starts with section--, in this case insert a
    section header as [value] and ignoring the key.
    :param config_file: path and filename of config file to update
    :param config: OrderedDict of options with possible section-- tags on index
    :param remove_all: list of entries to always remark out regardless
    :return:
    """
    file_descriptor, tempNamePath = mkstemp(prefix='rocknut')
    with open(config_file) as source_file_object, open(tempNamePath,
                                                       'w') as tempFileObject:
        # Copy existing config file line by line until complete or
        # the Rockstor header is found.
        # Also remark out any line containing a config option entry.
        # N.B. we don't deal well here with section headers above our header
        # but could just remark our all lines beginning with '[' but overkill.
        for line in source_file_object.readlines():
            if (not re.match('#', line)) and line.strip():
                # On non empty lines that don't begin with a "#" char look for
                # any occurrence of a config entry (split by space or =)
                words_in_line = line.split()
                if (any(word in config for word in words_in_line) or
                        any(word in config for word in line.split('=')) or
                        any(word in remove_all for word in words_in_line)):
                    # A config entry has been found so remark out that line to
                    # be safe (indented or otherwise).
                    tempFileObject.write('#' + line)
                else:
                    # Not remarked and not empty and not know to duplicate a
                    # config entry. Remark out to filter out unknown entries.
                    tempFileObject.write(line)
            elif (re.match(header, line) is None):
                # If the current line is not a Rockstor header then
                # write the source file line unchanged to the temp file.
                # N.B. This is a quick path for empty and remarked lines.
                tempFileObject.write(line)
            else:
                # We have found an existing rockstor header so break out.
                break
        # All source file lines above any Rockstor header have been processed.
        # Write a fresh Rockstor header and config to end of temp file so far
        tempFileObject.write('%s\n' % settings.NUT_HEADER)
        # now write out our config including section headers which should come
        # before their subsection counterparts courtesy of pre-processing.
        for option, value in config.items():
            if re.match("section--", option) is not None:
                # section header so surround value in [] and ignore option
                tempFileObject.write('[' + value + ']' + '\n')
                # no need to indent subsection as parser ignores white space:-
                # http://www.networkupstools.org/docs/user-manual.chunked/ar01s06.html
            else:
                # get our delimiter from nut_option_delimiter dict or use "="
                if option in nut_option_delimiter:
                    delimiter = nut_option_delimiter[option]
                else:
                    delimiter = "="
                tempFileObject.write(option + delimiter + value + '\n')
    # finally overwrite passed config file with the newly created temp file.
    move(tempNamePath, config_file)
