"""
Copyright (c) 2012-2023 Rockstor, Inc. <https://rockstor.com>
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
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

import json
import logging
import os
import re
import shutil
import stat
import sys
from tempfile import mkstemp

from django.conf import settings

from system import services
from system.osi import run_command, md5sum, replace_pattern_inline
from system.ssh import remove_sftp_server_subsystem, init_sftp_config
from system.constants import SYSTEMCTL
from collections import OrderedDict, namedtuple


logger = logging.getLogger(__name__)

BASE_DIR = settings.ROOT_DIR  # ends in "/"
BASE_BIN = f"{BASE_DIR}.venv/bin"
CONF_DIR = f"{BASE_DIR}conf"
DJANGO = f"{BASE_BIN}/django-admin"
DJANGO_MIGRATE_CMD = [DJANGO, "migrate", "--noinput"]
DJANGO_MIGRATE_SMART_MANAGER_CMD = DJANGO_MIGRATE_CMD + ["--database=smart_manager", "smart_manager"]
STAMP = f"{BASE_DIR}/.initrock"
FLASH_OPTIMIZE = f"{BASE_BIN}/flash-optimize"
DJANGO_PREP_DB = f"{BASE_BIN}/prep_db"
OPENSSL = "/usr/bin/openssl"
RPM = "/usr/bin/rpm"
YUM = "/usr/bin/yum"
IP = "/usr/sbin/ip"
# The collections, in order, of commands to run via "su - postgres -c"
#
# Our openSUSE systemd ExecStart= script runs 'initdb' for us, if required.
# And we (initrock.py) are run only after a successful postgresql systemd start:
# rockstor-pre.service has "After=postgresql.service & Requires=postgresql.service"
#
# Default Postgresql data dir: /var/lib/pgsql/data
# Default Postgresql log dir: /var/lib/pgsql/data/log/
#
# Configure host-based authentication (pg_hba.conf).
# md5 upscales to scram-sha-256 (released in pg10, default in pg13) hashes if found.
# See: https://www.postgresql.org/docs/13/auth-password.html
# Display the password hash: begins "md5" (old) or "SCRAM-SHA-256" (new)
# su - postgres -c "psql -c \"SELECT ROLPASSWORD FROM pg_authid WHERE rolname = 'rocky'\""
# su - postgres -c "psql -c \"ALTER ROLE rocky WITH PASSWORD 'rocky'\""

OVERWRITE_PG_HBA = f"cp -f {CONF_DIR}/pg_hba.conf /var/lib/pgsql/data/"
PG_RELOAD = "pg_ctl reload"  # Does not require pg_hba.conf based authentication.
RUN_SQL = "psql -w -f"  # Without password prompt and from file.
#
# We use psql the postgresql client command line program
# See: https://www.postgresql.org/docs/13/app-psql.html
#
# Tune Postgesql server to our needs.
DB_SYS_TUNE = OrderedDict()
DB_SYS_TUNE["Setup_host_based_auth"] = OVERWRITE_PG_HBA
DB_SYS_TUNE["Reload_config"] = PG_RELOAD  # Enables pg_hba for following psql access.
DB_SYS_TUNE["PG_tune"] = f"{RUN_SQL} {CONF_DIR}/postgresql_tune.sql"

# Create and then populate our databases (default & smart_manager) from scratch.
DB_SETUP = OrderedDict()
DB_SETUP["drop_and_recreate"] = f"{RUN_SQL} {CONF_DIR}/postgresql_setup.sql"
DB_SETUP["migrate_default"] = DJANGO_MIGRATE_CMD
DB_SETUP["migrate_smart_manager"] = DJANGO_MIGRATE_SMART_MANAGER_CMD

# List of systemd services to instantiate/update or remove, if required.
# Service filenames that are not found in CONF_DIR will be removed from the system.
SYSTEMD_DIR = "/usr/lib/systemd/system"
SYSTEMD_OVERRIDE_DIR = "/etc/systemd/system"

ROCKSTOR_SYSTEMD_SERVICES = [
    "rockstor-pre.service",  # Loads us (initrock.py).
    "rockstor.service",
    "rockstor-bootstrap.service",
]
# These services are added programatically outside initrock (rockstor-pre.service)
ROCKSTOR_EXTRA_SYSTEMD_SERVICES = [
    "rockstor-hdparm.service",  # Managed by system.osi.update_hdparm_service()
    "rockstor-fstrim.service",  # fstrim service and timer setup conditionally by
    "rockstor-fstrim.timer",  # scripts/flash_optimize.py
]
ROCKSTOR_LEGACY_SYSTEMD_SERVICES = [
    "rockstor-ipv6check.service",  # Legacy service from pre v4.1.0-0 development.
]

# Local files that need checking
# path: path to file.
# mask: use constants from the stat module to apply desired permissions to file.
#       use None to use the current mask of the target file defined at <path>.
# services: Python List of service(s) to restart, if any, after modifying the file.
LocalFile = namedtuple("LocalFile", "path mask services")
LOCAL_FILES = {
    "samba_config": LocalFile(
        path="/etc/samba/smb.conf", mask=None, services=["nmb", "smb"]
    ),
    "rockstor_crontab": LocalFile(
        path="/etc/cron.d/rockstortab", mask=stat.S_IRUSR | stat.S_IWUSR, services=None
    ),
    "replication_crontab": LocalFile(
        path="/etc/cron.d/replicationtab",
        mask=stat.S_IRUSR | stat.S_IWUSR,
        services=None,
    ),
}


def inet_addrs(interface=None):
    cmd = [IP, "addr", "show"]
    if interface is not None:
        cmd.append(interface)
    o, _, _ = run_command(cmd)
    ipaddr_list = []
    for l in o:
        if re.match("inet ", l.strip()) is not None:
            inet_fields = l.split()
            if len(inet_fields) > 1:
                ip_fields = inet_fields[1].split("/")
                if len(ip_fields) == 2:
                    ipaddr_list.append(ip_fields[0])
    return ipaddr_list


def current_rockstor_mgmt_ip(log):
    # importing here because, APIWrapper needs postgres to be setup, so
    # importing at the top results in failure the first time.
    from smart_manager.models import Service

    ipaddr = None
    port = 443
    so = Service.objects.get(name="rockstor")

    if so.config is not None:
        config = json.loads(so.config)
        port = config["listener_port"]
        try:
            ipaddr_list = inet_addrs(config["network_interface"])
            if len(ipaddr_list) > 0:
                ipaddr = ipaddr_list[0]
        except Exception as e:
            # interface vanished.
            log.exception(
                "Exception while gathering current management ip: {e}".format(e=e)
            )

    return ipaddr, port


def init_update_issue(log):
    ipaddr, port = current_rockstor_mgmt_ip(log)

    if ipaddr is None:
        ipaddr_list = inet_addrs()

    # We open w+ in case /etc/issue does not exist
    with open("/etc/issue", "w+") as ifo:
        if ipaddr is None and len(ipaddr_list) == 0:
            ifo.write("The system does not yet have an ip address.\n")
            ifo.write(
                "Rockstor cannot be configured using the web interface "
                "without this.\n\n"
            )
            ifo.write("Press Enter to receive updated network status\n")
            ifo.write(
                "If this message persists please login as root and "
                "configure your network using nmtui, then reboot.\n"
            )
        else:
            ifo.write("\nRockstor is successfully installed.\n\n")
            if ipaddr is not None:
                port_str = ""
                if port != 443:
                    port_str = ":{0}".format(port)
                ifo.write(
                    "web-ui is accessible with this link: "
                    "https://{0}{1}\n\n".format(ipaddr, port_str)
                )
            else:
                ifo.write("web-ui is accessible with the following links:\n")
                for i in ipaddr_list:
                    ifo.write("https://{0}\n".format(i))
    return ipaddr


def update_nginx(log):
    try:
        ip, port = current_rockstor_mgmt_ip(log)
        services.update_nginx(ip, port)
    except Exception as e:
        log.exception("Exception while updating nginx: {e}".format(e=e))


def update_tz(log):
    # update timezone variable in settings.py
    zonestr = os.path.realpath("/etc/localtime").split("zoneinfo/")[1]
    log.info("system timezone = {}".format(zonestr))
    sfile = "{}/src/rockstor/settings.py".format(BASE_DIR)
    fo, npath = mkstemp()
    updated = False
    with open(sfile) as sfo, open(npath, "w") as tfo:
        for line in sfo.readlines():
            if re.match("TIME_ZONE = ", line) is not None:
                curzone = line.strip().split("= ")[1].strip("'")
                if curzone == zonestr:
                    break
                else:
                    tfo.write("TIME_ZONE = '{}'\n".format(zonestr))
                    updated = True
                    log.info("Changed timezone from {} to {}".format(curzone, zonestr))
            else:
                tfo.write(line)
    if updated:
        shutil.move(npath, sfile)
    else:
        os.remove(npath)
    return updated


def bootstrap_sshd_config(log):
    """
    Setup sshd config options for Rockstor:
    1. Disable OS default (but not openssh default) of "Subsystem <path>sftp-server".
    2. Install "Subsystem sftp sftp-internal" required for Rockstor sftp access.
        Note that this turns the SFTP service ON by default.
    3. Add header line & "AllowUsers root" if conf/PermitRootLogin file exists.
    :param log:
    """
    conf_altered = remove_sftp_server_subsystem()
    if init_sftp_config():
        conf_altered = True
    if conf_altered:
        logger.info("SSHD config altered, restarting service")
        run_command([SYSTEMCTL, "restart", "sshd"])


def establish_shellinaboxd_service():
    """
    Normalise on shellinaboxd as service name for shellinabox package.
    The https://download.opensuse.org/repositories/shells shellinabox package
    ( https://build.opensuse.org/package/show/shells/shellinabox ) uses a
    systemd service name of shellinabox.
    If we find no shellinaboxd service file and there exists a shellinabox one
    create a copy to enable us to normalise on shellinaboxd and avoid carrying
    another package just to implement this service name change as we are
    heavily invested in the shellinaboxd service name.
    :return: Indication of action taken
    :rtype: Boolean
    """
    logger.info("Normalising on shellinaboxd service file")
    required_sysd_name = "/usr/lib/systemd/system/shellinaboxd.service"
    opensuse_sysd_name = "/usr/lib/systemd/system/shellinabox.service"
    if os.path.exists(required_sysd_name):
        logger.info("- shellinaboxd.service already exists")
        return False
    if os.path.exists(opensuse_sysd_name):
        shutil.copyfile(opensuse_sysd_name, required_sysd_name)
        logger.info("- established shellinaboxd.service file")
        return True


def establish_rockstor_nginx_overide_conf():
    """
    We use a systemd drop-in override configuration file to have nginx configured
    as we required via an ExecStart nginx configuration file directive (-c).
    :return: Indication of action taken
    :rtype: Boolean
    """
    logger.info("Establishing Rockstor nginx service override file")
    override_path = "{}/nginx.service.d".format(SYSTEMD_OVERRIDE_DIR)
    return install_or_update_systemd_service(
        "30-rockstor-nginx-override.conf", "nginx", override_path
    )


def move_or_remove_legacy_rockstor_service_files():
    """
    Prior to v4.5.1-0 we placed rockstor* services in /etc/systemd/system which
    as per https://en.opensuse.org/openSUSE:Systemd_packaging_guidelines#Unit_files
    in incorrect. We now locate our unique rockstor* services in the recommended
    /usr/lib/systemd/system and only use /etc/systemd/systemd for overrides.
    #
    Address update by moving all non legacy non-override rockstor* unit files.
    Legacy rockstor* unit files are remove.
    :return: Indication of action taken
    :rtype: Boolean
    """
    conf_altered = False
    # Base services plus extra/legacy services
    for service_file_name in (
        ROCKSTOR_SYSTEMD_SERVICES
        + ROCKSTOR_EXTRA_SYSTEMD_SERVICES
        + ROCKSTOR_LEGACY_SYSTEMD_SERVICES
    ):
        target_with_path = "{}/{}".format(SYSTEMD_OVERRIDE_DIR, service_file_name)
        if os.path.isfile(target_with_path):
            if service_file_name not in ROCKSTOR_LEGACY_SYSTEMD_SERVICES:
                logger.info(
                    "Moving {} from {} to {}".format(
                        service_file_name, SYSTEMD_OVERRIDE_DIR, SYSTEMD_DIR
                    )
                )
                shutil.move(
                    target_with_path,
                    "{}/{}".format(SYSTEMD_DIR, service_file_name),
                )
            else:
                logger.info("{} stop/disable/remove (LEGACY).".format(target_with_path))
                run_command(
                    [SYSTEMCTL, "stop", service_file_name], throw=False
                )  # allow for not loaded
                run_command([SYSTEMCTL, "disable", service_file_name])
                os.remove(target_with_path)
            conf_altered = True
    return conf_altered


def establish_systemd_services():
    """
    Wrapper to establish our various systemd services.
    """
    conf_altered = establish_shellinaboxd_service()
    if move_or_remove_legacy_rockstor_service_files():
        conf_altered = True
    if establish_rockstor_nginx_overide_conf():
        conf_altered = True
    for service_file_name in ROCKSTOR_SYSTEMD_SERVICES:
        if install_or_update_systemd_service(service_file_name):
            conf_altered = True
    # Make systemd aware of our changes, if any:
    # See: https://www.freedesktop.org/software/systemd/man/systemd.generator.html
    if conf_altered:
        logger.info("Systemd config altered, running daemon-reload")
        run_command([SYSTEMCTL, "daemon-reload"])


def install_or_update_systemd_service(
    filename, service_name=None, target_directory=SYSTEMD_DIR
):
    """
    Generic systemd service file installer/updater.
    Uses file existence and checksums to establish if install or an update is required.
    :return: Indication of action taken
    :rtype: Boolean
    """
    if service_name is None:
        service_name = filename
    target_csum = "na"
    source_with_path = "{}/{}".format(CONF_DIR, filename)
    target_with_path = "{}/{}".format(target_directory, filename)
    if not os.path.isfile(source_with_path):
        if os.path.isfile(target_with_path):
            logger.info(
                "{} stopping, disabling, and removing as legacy.".format(
                    target_with_path
                )
            )
            run_command(
                [SYSTEMCTL, "stop", service_name], throw=False
            )  # allow for not loaded
            run_command([SYSTEMCTL, "disable", service_name])
            os.remove(target_with_path)
            logger.info("{} removed.".format(filename))
            return True
        else:
            logger.debug("Legacy {} already removed.".format(filename))
            return False
    source_csum = md5sum(source_with_path)
    if os.path.isfile(target_with_path):
        target_csum = md5sum(target_with_path)
    if not (source_csum == target_csum):
        # create our target_directory if it doesn't exist.
        if not os.path.isdir(target_directory):
            os.mkdir(target_directory)
        shutil.copyfile(source_with_path, target_with_path)
        logger.info("{} updated.".format(target_with_path))
        run_command([SYSTEMCTL, "enable", service_name])
        return True
    logger.info("{} up-to-date.".format(target_with_path))
    return False


def establish_poetry_paths():
    """Ensure path to Rockstor's binaries point to Poetry venv

    Before our move to Poetry, our binaries lived in /opt/rockstor/bin.
    After our move to Poetry, these now reside in /opt/rockstor/.venv/bin.
    While the generation of new local files using these paths account for these
    new paths, pre-existing files still use the non-existent old paths.
    This function checks for these local files and changes them accordingly. If one
    or more systemd service is associated to these files, it restarts it/them if the
    given service(s) is/are currently active.
    The local files in questions are defined in the LOCAL_FILES constant.
    """
    logger.info("### BEGIN Establishing poetry path to binaries in local files...")
    pattern = "/opt/rockstor/bin/"
    replacement = "/opt/rockstor/.venv/bin/"
    for local_file in LOCAL_FILES:
        if os.path.isfile(LOCAL_FILES[local_file].path):
            fh, npath = mkstemp()
            altered = replace_pattern_inline(
                LOCAL_FILES[local_file].path, npath, pattern, replacement
            )
            if altered:
                if LOCAL_FILES[local_file].mask is not None:
                    logger.debug(
                        "Set {} to mask {}".format(
                            local_file, oct(LOCAL_FILES[local_file].mask)
                        )
                    )
                    os.chmod(npath, LOCAL_FILES[local_file].mask)
                else:
                    shutil.copystat(LOCAL_FILES[local_file].path, npath)
                shutil.move(npath, LOCAL_FILES[local_file].path)
                logger.info(
                    "The path to binaries in {} ({}) has been updated.".format(
                        local_file, LOCAL_FILES[local_file].path
                    )
                )
                if LOCAL_FILES[local_file].services is not None:
                    for service in LOCAL_FILES[local_file].services:
                        if services.is_systemd_service_active(service):
                            logger.info(
                                "The {} service is currently active... restart it".format(
                                    service
                                )
                            )
                            run_command([SYSTEMCTL, "restart", service], log=True)
            else:
                os.remove(npath)
                logger.info("{} already looks good.".format(local_file))
        else:
            logger.info(
                "The {} ({}) could not be found".format(
                    local_file, LOCAL_FILES[local_file].path
                )
            )
    logger.info("### DONE establishing poetry path to binaries in local files.")


def main():
    loglevel = logging.INFO
    if len(sys.argv) > 1 and sys.argv[1] == "-x":
        loglevel = logging.DEBUG
    logging.basicConfig(format="%(asctime)s: %(message)s", level=loglevel)

    cert_loc = "{}/certs/".format(BASE_DIR)
    if os.path.isdir(cert_loc):
        if not os.path.isfile(
            "{}/rockstor.cert".format(cert_loc)
        ) or not os.path.isfile("{}/rockstor.key".format(cert_loc)):
            shutil.rmtree(cert_loc)

    if not os.path.isdir(cert_loc):
        os.mkdir(cert_loc)
        dn = (
            "/C=US/ST=Rockstor user's state/L=Rockstor user's "
            "city/O=Rockstor user/OU=Rockstor dept/CN=rockstor.user"
        )
        logging.info("Creating openssl cert...")
        run_command(
            [
                OPENSSL,
                "req",
                "-nodes",
                "-newkey",
                "rsa:2048",
                "-keyout",
                "{}/first.key".format(cert_loc),
                "-out",
                "{}/rockstor.csr".format(cert_loc),
                "-subj",
                dn,
            ]
        )
        logging.debug("openssl cert created")
        logging.info("Creating rockstor key...")
        run_command(
            [
                OPENSSL,
                "rsa",
                "-in",
                "{}/first.key".format(cert_loc),
                "-out",
                "{}/rockstor.key".format(cert_loc),
            ]
        )
        logging.debug("rockstor key created")
        logging.info("Singing cert with rockstor key...")
        run_command(
            [
                OPENSSL,
                "x509",
                "-in",
                "{}/rockstor.csr".format(cert_loc),
                "-out",
                "{}/rockstor.cert".format(cert_loc),
                "-req",
                "-signkey",
                "{}/rockstor.key".format(cert_loc),
                "-days",
                "3650",
            ]
        )
        logging.debug("cert signed.")
        logging.info("restarting nginx...")
        run_command([SYSTEMCTL, "restart", "nginx"])

    logging.info("Checking for flash and Running flash optimizations if appropriate.")
    run_command([FLASH_OPTIMIZE, "-x"], throw=False)
    try:
        logging.info("Updating the timezone from the system")
        update_tz(logging)
    except Exception as e:
        logging.error("Exception while updating timezone: {}".format(e.__str__()))
        logging.exception(e)

    try:
        logging.info("Initialising SSHD config")
        bootstrap_sshd_config(logging)
    except Exception as e:
        logging.error("Exception while updating sshd config: {}".format(e.__str__()))

    db_already_setup = os.path.isfile(STAMP)
    for db_stage_name, db_stage_items in zip(
        ["Tune Postgres", "Setup Databases"], [DB_SYS_TUNE, DB_SETUP]
    ):
        if db_stage_name == "Setup Databases" and db_already_setup:
            continue
        logging.info(f"--DB-- {db_stage_name} --DB--")
        for action, command in db_stage_items.items():
            logging.info(f"--DB-- Running - {action}")
            if action.startswith("migrate"):
                run_command(command)
            else:
                run_command(["su", "-", "postgres", "-c", command])
            logging.info(f"--DB-- Done with {action}.")
        logging.info(f"--DB-- {db_stage_name} Done --DB--.")
        if db_stage_name == "Setup Databases":
            run_command(["touch", STAMP])  # file flag indicating db setup

    logging.info("Running app database migrations...")
    fake_migration_cmd = DJANGO_MIGRATE_CMD + ["--fake"]
    fake_initial_migration_cmd = DJANGO_MIGRATE_CMD + ["--fake-initial"]

    # Migrate Content types before individual apps
    logger.debug("migrate (--fake-initial) contenttypes")
    run_command(
        fake_initial_migration_cmd + ["--database=default", "contenttypes"], log=True
    )

    for app in ("storageadmin", "smart_manager"):
        db = "default"
        if app == "smart_manager":
            db = app
        o, e, rc = run_command(
            [DJANGO, "showmigrations", "--list", "--database={}".format(db), app]
        )
        initial_faked = False
        for l in o:
            if l.strip() == "[X] 0001_initial":
                initial_faked = True
                break
        if not initial_faked:
            db_arg = "--database={}".format(db)
            logger.debug(
                "migrate (--fake) db=({}) app=({}) 0001_initial".format(db, app)
            )
            run_command(fake_migration_cmd + [db_arg, app, "0001_initial"], log=True)

    run_command(DJANGO_MIGRATE_CMD + ["auth"], log=True)
    run_command(DJANGO_MIGRATE_CMD + ["storageadmin"], log=True)
    run_command(DJANGO_MIGRATE_SMART_MANAGER_CMD, log=True)

    # Avoid re-apply from our six days 0002_08_updates to oauth2_provider
    # by faking so we can catch-up on remaining migrations.
    # Only do this if not already done, however, as we would otherwise incorrectly reset
    # the list of migrations applied (https://github.com/rockstor/rockstor-core/issues/2376).
    oauth2_provider_faked = False
    # Get current list of migrations
    o, e, rc = run_command([DJANGO, "showmigrations", "--list", "oauth2_provider"])
    for l in o:
        if l.strip() == "[X] 0002_08_updates":
            logger.debug(
                "The 0002_08_updates migration seems already applied, so skip it"
            )
            oauth2_provider_faked = True
            break
    if not oauth2_provider_faked:
        logger.debug(
            "The 0002_08_updates migration is not already applied so fake apply it now"
        )
        run_command(
            fake_migration_cmd + ["oauth2_provider", "0002_08_updates"], log=True
        )

    # Run all migrations for oauth2_provider
    run_command(DJANGO_MIGRATE_CMD + ["oauth2_provider"], log=True)

    logging.info("DB Migrations Done")

    logging.info("Running Django prep_db.")
    run_command([DJANGO_PREP_DB])
    logging.info("Done")

    logging.info("Stopping firewalld...")
    run_command([SYSTEMCTL, "stop", "firewalld"])
    run_command([SYSTEMCTL, "disable", "firewalld"])
    logging.info("Firewalld stopped and disabled")

    logging.info("Enabling and Starting atd...")
    run_command([SYSTEMCTL, "enable", "atd"])
    run_command([SYSTEMCTL, "start", "atd"])
    logging.info("Atd enabled and started")

    update_nginx(logging)

    init_update_issue(logging)

    establish_systemd_services()

    establish_poetry_paths()


if __name__ == "__main__":
    main()
