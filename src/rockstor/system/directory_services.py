"""
Copyright (c) 2012-2023 RockStor, Inc. <https://rockstor.com>
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

import os
import stat

import re

from system.osi import append_to_line, run_command
from tempfile import mkstemp
from shutil import move
import logging

from system.services import systemctl

logger = logging.getLogger(__name__)

NSSWITCH_FILE = "/etc/nsswitch.conf"
SSSD_FILE = "/etc/sssd/sssd.conf"
NET = "/usr/bin/net"
REALM = "/usr/sbin/realm"
ADCLI = "/usr/sbin/adcli"
OPENSSL = "/usr/bin/openssl"


def validate_tls_cert(server, cert):
    """
    Run openssl s_client -connect server:389 -CAfile path-to-cert
    to verify the provided TLS certificate against the LDAP server.
    :param server: String - FQDN of the LDAP server
    :param cert: String - Absolute path to the TLS certificate
    :return:
    """
    cmd = [
        OPENSSL,
        "s_client",
        "-connect",
        "{}:389".format(server),
        "-CAfile",
        cert,
    ]
    o, e, rc = run_command(cmd, throw=False)
    if "Verification: OK" not in o:
        err_msg = (
            "Failed to validate the TLS certificate ({}).\n"
            "out: {} err: {} rc: {}".format(cert, o, e, rc)
        )
        if any("fopen:No such file or directory" in err for err in e):
            err_msg = (
                "The TLS certificate file could not be found at {}.\n"
                "out: {} err: {} rc: {}".format(cert, o, e, rc)
            )
        raise Exception(err_msg)


def update_nss(databases, provider, remove=False):
    """
    Update the nss configuration file (NSSWITCH_FILE) to include a
    given provider ("sss", for instance) to one or more databases.
    :param databases: List - databases to be updated (e.g. ["passwd", "group"])
    :param provider: String - provider to be used (e.g. "sss")
    :param remove: Boolean - Remove provider from databases if True
    :return:
    """
    fo, npath = mkstemp()
    sep = " "
    dbs = [db + ":" for db in databases]
    append_to_line(NSSWITCH_FILE, npath, dbs, provider, sep, remove)
    move(npath, NSSWITCH_FILE)
    # Set file to rw- r-- r-- (644) via stat constants.
    os.chmod(NSSWITCH_FILE, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    logger.debug(
        "The {} provider to the {} databases has been updated in {}".format(
            provider, databases, NSSWITCH_FILE
        )
    )


def sssd_update_ad(domain, config):
    """
    Add enumerate = True in sssd so user/group lists will be
    visible on the web-ui.
    :param domain: String - Domain to which the update should apply
    :param config: Dict - Active Directory service configuration
    :return:
    """
    el = "enumerate = True\n"
    csl = "case_sensitive = True\n"
    opts = []
    if config.get("enumerate") is True:
        opts.append(el)
    if config.get("case_sensitive") is True:
        opts.append(csl)
    ol = "".join(opts)
    fh, npath = mkstemp()
    with open(SSSD_FILE) as sfo, open(npath, "w") as tfo:
        domain_section = False
        for line in sfo.readlines():
            if domain_section is True:
                if len(line.strip()) == 0 or line[0] == "[":
                    # empty line or new section without empty line before it.
                    tfo.write(ol)
                    domain_section = False
            elif re.match("\[domain/%s]" % domain, line) is not None:
                domain_section = True
            tfo.write(line)
        if domain_section is True:
            # reached end of file, also coinciding with end of domain section
            tfo.write(ol)
    move(npath, SSSD_FILE)
    # Set file to rw- --- --- (600) via stat constants.
    os.chmod(SSSD_FILE, stat.S_IRUSR | stat.S_IWUSR)
    logger.debug(
        "The configuration of the {} domain in {} has been updated".format(
            domain, SSSD_FILE
        )
    )
    systemctl("sssd", "restart")


def sssd_add_ldap(ldap_params):
    """
    Write to sssd.conf all parameters required for connecting to an ldap server.
    :param ldap_params: Dict
    :return:
    """
    # Prepare options to write
    server = ldap_params["server"]
    opts = {
        "ldap_id_use_start_tls": "True",
        "cache_credentials": "True",
        "ldap_search_base": "{}".format(ldap_params["basedn"]),
        "id_provider": "ldap",
        "auth_provider": "ldap",
        "chpass_provider": "ldap",
        "ldap_uri": "{}".format(ldap_params["ldap_uri"]),
        "ldap_tls_reqcert": "demand",
        "ldap_tls_cacert": "{}".format(ldap_params["cacertpath"]),
        "ldap_tls_cacertdir": "{}".format(ldap_params["cacert_dir"]),
        "enumerate": "{}".format(ldap_params["enumerate"]),
    }
    # Write to file
    fh, npath = mkstemp()
    with open(SSSD_FILE) as sfo, open(npath, "w") as tfo:
        sssd_section = False
        domain_section = False
        for line in sfo.readlines():
            if sssd_section is True:
                if re.match("domains = ", line) is not None:
                    line = "".join([line.strip(), " {}\n".format(server)])
                    sssd_section = False
                elif len(line.strip()) == 0:
                    tfo.write("domains = {}\n".format(server))
                    sssd_section = False
            elif domain_section is True:
                for k, v in opts.items():
                    if re.match(k, line) is None:
                        tfo.write("{} = {}\n".format(k, v))
            elif re.match("\[sssd]", line) is not None:
                sssd_section = True
            elif re.match("\[domain/{}]".format(server), line) is not None:
                domain_section = True
            tfo.write(line)
        if domain_section is False:
            # reached end of file, also coinciding with end of domain section
            tfo.write("\n[domain/{}]\n".format(server))
            for k, v in opts.items():
                tfo.write("{} = {}\n".format(k, v))
    move(npath, SSSD_FILE)
    # Set file to rw- --- --- (600) via stat constants.
    os.chmod(SSSD_FILE, stat.S_IRUSR | stat.S_IWUSR)
    logger.debug(
        "The configuration of the {} domain in {} has been updated".format(
            server, SSSD_FILE
        )
    )
    systemctl("sssd", "restart")


def sssd_remove_ldap(server):
    """
    Removes any configuration pertaining to "server" from sssd.conf
    thereby unconfiguring the LDAP server. We thus need to remove it
    from the list of domains in the [sssd] section, and then remove
    its own section titled [domain/server].
    :param server: String -
    :return:
    """
    fh, npath = mkstemp()
    with open(SSSD_FILE) as sfo, open(npath, "w") as tfo:
        sssd_section = False
        domain_section = False
        for line in sfo.readlines():
            if sssd_section is True:
                if re.match("domains = ", line) is not None:
                    tfo.write(line.replace(server, ""))
                    sssd_section = False
                    continue
            elif domain_section is True:
                continue
            elif re.match("\[sssd]", line) is not None:
                sssd_section = True
            elif re.match("\[domain/{}]".format(server), line) is not None:
                domain_section = True
                continue
            elif len(line.strip()) == 0:
                # empty line
                domain_section = False
            tfo.write(line)
    move(npath, SSSD_FILE)
    # Set file to rw- --- --- (600) via stat constants.
    os.chmod(SSSD_FILE, stat.S_IRUSR | stat.S_IWUSR)
    logger.debug(
        "The configuration of the {} domain in {} has been removed".format(
            server, SSSD_FILE
        )
    )


def sssd_update_services(service, remove=False):
    """
    Update the list of sssd services.
    :param service: String - name of the service to be updated
    :param remove: Boolean - Remove from list of services if True
    """
    fo, npath = mkstemp()
    sep = ", "
    pattern = ["services = "]
    append_to_line(SSSD_FILE, npath, pattern, service, sep, remove)
    move(npath, SSSD_FILE)
    # Set file to rw- --- --- (600) via stat constants.
    os.chmod(SSSD_FILE, stat.S_IRUSR | stat.S_IWUSR)
    logger.debug("The {} service has been added to {}".format(service, SSSD_FILE))
    systemctl("sssd", "restart")


def join_domain(config, method="sssd"):
    """
    Join an Active Directory domain.
    :param config: Dict - gathered from the AD service config
    :param method: String - SSSD or Winbind (default is sssd)
    :return:
    """
    domain = config.get("domain")
    admin = config.get("username")
    cmd = [REALM, "join", "-U", admin, domain]
    cmd_options = [
        "--membership-software=samba",
    ]
    if config.get("no_ldap_id_mapping") is True:
        cmd_options.append("--automatic-id-mapping=no")
    cmd[-3:-3] = cmd_options
    if method == "winbind":
        cmd = [NET, "ads", "join", "-U", admin]
    return run_command(cmd, input=("{}\n".format(config.get("password"))), log=True)


def leave_domain(config, method="sssd"):
    """
    Leave a configured Active Directory domain.
    :param config: Dict - gathered from the AD service config
    :param method: String - SSSD or Winbind (default is sssd)
    :return:
    """
    pstr = "{}\n".format(config.get("password"))
    cmd = [REALM, "leave", config.get("domain")]
    if method == "winbind":
        cmd = [NET, "ads", "leave", "-U", config.get("username")]
        try:
            return run_command(cmd, input=pstr)
        except:
            status_cmd = [NET, "ads", "status", "-U", config.get("username")]
            o, e, rc = run_command(status_cmd, input=pstr, throw=False)
            if rc != 0:
                return logger.debug(
                    "Status shows not joined. out: %s err: %s rc: %d" % (o, e, rc)
                )
            raise
    else:
        run_command(cmd, log=True)


def domain_workgroup(domain: str, method: str = "sssd") -> str:
    """
    Fetches the Workgroup value from an Active Directory domain
    to be fed to Samba configuration.
    :param domain: String - Active Directory domain
    :param method: String - SSSD or Winbind (default is sssd)
    :return:
    """
    cmd = [NET, "ads", "workgroup", f"--realm={domain.upper()}"]
    match_str = "Workgroup:"
    if method == "winbind":
        cmd = [ADCLI, "info", domain]
        match_str = "domain-short = "
    o, e, rc = run_command(cmd, log=True)
    for line in o:
        line = line.strip()
        if re.match(match_str, line) is not None:
            return line.split(match_str)[1].strip()
    raise Exception(f"Failed to retrieve Workgroup. out: {o} err: {e} rc: {rc}")


def validate_idmap_range(config):
    default_range = "10000 - 999999"
    idmap_range = config.get("idmap_range", "10000 - 999999")
    idmap_range = idmap_range.strip()
    if len(idmap_range) > 0:
        rfields = idmap_range.split()
        if len(rfields) != 3:
            raise Exception(
                "Invalid idmap range. valid format is "
                "two integers separated by a -. eg: "
                "10000 - 999999"
            )
        try:
            rlow = int(rfields[0].strip())
            rhigh = int(rfields[2].strip())
        except Exception as e:
            raise Exception(
                "Invalid idmap range. Numbers in the "
                "range must be valid integers. "
                "Error: {}.".format(e.__str__())
            )
        if rlow >= rhigh:
            raise Exception(
                "Invalid idmap range. Numbers in the "
                "range must go from low to high. eg: "
                "10000 - 999999"
            )
    else:
        config["idmap_range"] = default_range
