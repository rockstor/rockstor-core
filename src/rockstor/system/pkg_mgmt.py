"""
Copyright (c) 2012-2020 RockStor, Inc. <http://rockstor.com>
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
import platform
import re
import stat
from tempfile import mkstemp
from osi import run_command
from services import systemctl
import shutil
import time
from datetime import datetime, timedelta
import requests
from django.conf import settings
from system.exceptions import CommandException
import distro
import logging

logger = logging.getLogger(__name__)

YUM = "/usr/bin/yum"
RPM = "/usr/bin/rpm"
ZYPPER = "/usr/bin/zypper"
SYSTEMCTL = "/usr/bin/systemctl"
AT = "/usr/bin/at"
YCFILE = "/etc/yum/yum-cron.conf"  # Doesn't exist in openSUSE


def install_pkg(name):
    return run_command([YUM, "--setopt=timeout=600", "-y", "install", name])


def downgrade_pkgs(*packages):
    cmd = [YUM, "--setopt=timeout=600", "-y", "downgrade"]
    for p in packages:
        cmd.append(p)
    return run_command(cmd)


def auto_update(enable=True):
    # TODO: Add openSUSE zypper equivalent
    service = "yum-cron"
    fo, npath = mkstemp()
    updated = False
    with open(YCFILE) as ifo, open(npath, "w") as tfo:
        for line in ifo.readlines():
            if re.match("apply_updates = ", line) is not None:
                if enable:
                    tfo.write("apply_updates = yes\n")
                else:
                    tfo.write("apply_updates = no\n")
                updated = True
            else:
                tfo.write(line)
    if not updated:
        raise Exception(
            "apply_updates directive missing in {}, assuming it "
            "is corrupt. No change made.".format(YCFILE)
        )
    shutil.move(npath, YCFILE)
    if enable:
        systemctl(service, "enable")
        systemctl(service, "start")
    else:
        systemctl(service, "stop")
        systemctl(service, "disable")


def auto_update_status():
    enabled = False
    with open(YCFILE) as ifo:
        for line in ifo.readlines():
            if re.match("apply_updates = yes", line) is not None:
                enabled = True
                break
    if enabled:
        systemctl("yum-cron", "status")
    return enabled


def current_version():
    out, err, rc = run_command([RPM, "-qi", "rockstor"], throw=False)
    if rc != 0:
        return "0.0-0"
    return "{}-{}".format(out[1].split(":")[-1].strip(), out[2].split(":")[-1].strip())


def rpm_build_info(pkg):
    version = "Unknown Version"
    date = None
    distro_id = distro.id()
    try:
        o, e, rc = run_command([YUM, "info", "installed", "-v", pkg])
    except CommandException as e:
        # Catch "No matching Packages to list" so we can return:
        # "Unknown Version", None
        emsg = "Error: No matching Packages to list"
        # By checking both the first error element and the second to last we
        # catch one yum waiting for another to release yum lock.
        if e.err[0] == emsg or e.err[-2] == emsg:
            logger.info('No "rockstor" package found: source install?')
            return version, date
        # otherwise we raise an exception as normal.
        raise e
    for l in o:
        if re.match("Buildtime", l) is not None:
            # Legacy Rockstor (using original yum):
            #     "Buildtime   : Tue Dec  5 13:34:06 2017"
            # openSUSE Rocsktor (using dnf-yum):
            #     "Buildtime    : Fri 29 Nov 2019 18:34:43 GMT"
            # we return 2017-Dec-06 or 2019-Nov-29
            # Note the one day on from retrieved Buildtime with zero padding.
            dfields = l.strip().split()
            if distro_id == "rockstor":  # CentOS based Rockstor conditional
                dstr = dfields[6] + " " + dfields[3] + " " + dfields[4]
            else:  # Assuming we are openSUSE variant and so using dnf-yum
                dstr = dfields[5] + " " + dfields[4] + " " + dfields[3]
            bdate = datetime.strptime(dstr, "%Y %b %d")
            bdate += timedelta(days=1)
            date = bdate.strftime("%Y-%b-%d")
        if re.match("Version ", l) is not None:
            version = l.strip().split()[2]
        if re.match("Release ", l) is not None:
            version = "{}-{}".format(version, l.strip().split()[2])
    return version, date


def zypper_repos_list():
    """
    Low level wrapper around "zypper repos"
    :return: List of repo Alias's
    """
    repo_list = []
    cmd = [ZYPPER, "-q", "repos"]
    out, err, rc = run_command(cmd, log=True)
    if len(out) > 0 and rc == 0:
        for line in out:
            # Skip empty or header lines
            if len(line) == 0 or line[0] == "#" or line[0] == "-":
                continue
            line_fields = line.split()
            if len(line_fields) >= 3:
                repo_list.append(line_fields[2])
    return repo_list


def switch_repo(subscription, on=True):
    repos_dir = "/etc/yum.repos.d"
    yum_file = "{}/Rockstor-{}.repo".format(repos_dir, subscription.name)
    rock_pub_key_file = "{}conf/ROCKSTOR-GPG-KEY".format(settings.ROOT_DIR)
    # Historically our base subscription url denotes our CentOS rpm repo.
    subscription_distro_url = subscription.url
    distro_id = distro.id()
    machine_arch = platform.machine()
    use_zypper = True
    repo_alias = "Rockstor-{}".format(subscription.name)
    logger.debug("########### SWITCH REPO repo-alias = {}".format(repo_alias))
    if distro_id == "opensuse-leap":
        subscription_distro_url += "/leap/{}".format(distro.version())
    elif distro_id == "opensuse-tumbleweed":
        subscription_distro_url += "/tumbleweed"
    else:
        use_zypper = False
    if machine_arch != "x86_64":
        subscription_distro_url += "_{}".format(machine_arch)
    # Check if dir /etc/yum.repos.d exists and if not create.
    if not os.path.isdir(repos_dir):
        # Can use os.makedirs(path) if intermediate levels also don't exist.
        os.mkdir(repos_dir)
    if subscription.password is not None:
        repo_url = "http://{}:{}@{}".format(
            subscription.appliance.uuid, subscription.password, subscription_distro_url
        )
    else:
        repo_url = "http://{}".format(subscription_distro_url)
    if on:
        if use_zypper:
            run_command([RPM, "--import", rock_pub_key_file], log=True)
            current_repo_list = zypper_repos_list()
            if subscription.name == "Stable" and repo_alias not in current_repo_list:
                if "Rockstor-Testing" in current_repo_list:
                    run_command([ZYPPER, "removerepo", "Rockstor-Testing"])
                # If already added rc=4
                run_command(
                    [ZYPPER, "addrepo", "--refresh", repo_url, repo_alias],
                    log=True,
                    throw=False,
                )
            if subscription.name == "Testing" and repo_alias not in zypper_repos_list():
                if "Rockstor-Stable" in current_repo_list:
                    run_command([ZYPPER, "removerepo", "Rockstor-Stable"])
                # If already added rc=4
                run_command(
                    [ZYPPER, "addrepo", "--refresh", repo_url, repo_alias],
                    log=True,
                    throw=False,
                )
        # N.B. for now we also use YUM (read only) on openSUSE
        with open(yum_file, "w") as rfo:
            rfo.write("[Rockstor-{}]\n".format(subscription.name))
            rfo.write("name={}\n".format(subscription.description))
            rfo.write("baseurl={}\n".format(repo_url))
            rfo.write("enabled=1\n")
            rfo.write("gpgcheck=1\n")
            rfo.write("gpgkey=file://{}\n".format(rock_pub_key_file))
            rfo.write("metadata_expire=1h\n")
        # Set file to rw- --- --- (600) via stat constants.
        os.chmod(yum_file, stat.S_IRUSR | stat.S_IWUSR)
    else:
        if os.path.exists(yum_file):
            os.remove(yum_file)
        if use_zypper:
            run_command(
                [ZYPPER, "removerepo", "Rockstor-Testing", "Rockstor-Stable"], log=True
            )


def repo_status(subscription):
    if subscription.password is None:
        return "active", "public repo"
    try:
        res = requests.get(
            "http://{}".format(subscription.url),
            auth=(subscription.appliance.uuid, subscription.password),
        )
        if res.status_code == 401:
            return "inactive", res.text
        elif res.status_code == 200:
            return "active", res.text
        return res.status_code, res.text
    except requests.ConnectionError as e:
        e_msg = (
            "Failed to connect to {}. Is the Rockstor system connected "
            "to the internet?. Lower level exception: {}".format(
                subscription.url, e.__str__()
            )
        )
        raise Exception(e_msg)


def rockstor_pkg_update_check(subscription=None):
    distro_id = distro.id()
    machine_arch = platform.machine()
    if subscription is not None:
        switch_repo(subscription)
    pkg = "rockstor"
    version, date = rpm_build_info(pkg)
    if date is None:
        # None date signifies no rpm installed so list all changelog entries.
        date = "all"
    log = False
    available = False
    new_version = None
    updates = []
    if distro_id == "rockstor":
        changelog_cmd = [YUM, "changelog", date, pkg]
    else:  # We are assuming openSUSE with dnf-yum specific options
        if date != "all":
            changelog_cmd = [YUM, "changelog", "--since", date, pkg]
        else:
            # Here we list the default number of changelog entries:
            # defaults to last 8 releases but states "Listing all changelogs"
            changelog_cmd = [YUM, "changelog", pkg]
    try:
        o, e, rc = run_command(changelog_cmd)
    except CommandException as e:
        # Catch as yet unconfigured repos ie openSUSE Stable error log accordingly.
        # Avoids breaking current version display and update channel selection.
        emsg = "Error\\: Cannot retrieve repository metadata \\(repomd.xml\\)"
        if re.match(emsg, e.err[-2]) is not None:
            logger.error(
                "Rockstor repo for distro.id ({}) version ({}) may "
                "not exist: pending or deprecated.\nReceived: ({}).".format(
                    distro_id, distro.version(), e.err
                )
            )
            new_version = version  # Explicitly set (flag) for code clarity.
            return version, new_version, updates
        # otherwise we raise an exception as normal.
        raise e
    for l in o:
        # We have possible targets of:
        # "Listing changelogs since 2019-11-29" - legacy yum and dnf-yum
        # "Listing all changelogs" - legacy yum and dnf-yum with no --count=#
        # "Listing # latest changelogs" - dnf-yum with a --count=# options
        if re.match("Listing", l) is not None:
            available = True
        if not available:
            continue
        if new_version is None:
            if re.match("rockstor-", l) is not None:  # legacy yum
                # eg: "rockstor-3.9.2-51.2089.x86_64"
                new_version = (
                    l.split()[0]
                    .split("rockstor-")[1]
                    .split(".{}".format(machine_arch))[0]
                )
            if re.match("Changelogs for rockstor-", l) is not None:  # dnf-yum
                # eg: "Changelogs for rockstor-3.9.2-51.2089.x86_64"
                new_version = (
                    l.split()[2]
                    .split("rockstor-")[1]
                    .split(".{}".format(machine_arch))[0]
                )
        if log is True:
            updates.append(l)
            if len(l.strip()) == 0:
                log = False
        if re.match("\* ", l) is not None:
            updates.append(l)
            log = True
    if new_version is None:
        logger.debug("No changelog found: trying yum update for info.")
        # Do a second check which is valid for updates without changelog
        # updates. eg: same day updates, testing updates.
        new_version = pkg_latest_available(pkg, machine_arch, distro_id)
        if new_version is None:
            new_version = version
    return version, new_version, updates


def pkg_latest_available(pkg_name, arch, distro_id):
    """
    Simple wrapper around "yum update pkg_name --assumeno" to retrieve
    latest version available from "Version" column
    :return:
    """
    new_version = None
    # TODO: We might use "zypper se -s --match-exact rockstor" and parse first
    #  line with rockstor in second column but unit test will be defunct.
    #  Advantage: works with no rockstor version installed, no so dnf-yum
    o, e, rc = run_command([YUM, "update", pkg_name, "--assumeno"], throw=False)
    if rc == 1:
        for l in o:
            if distro_id == "rockstor":
                # Legacy Yum appropriate parsing, all info on one line.
                # "Package rockstor.x86_64 0:3.9.2-51.2089 will be an update"
                if re.search("will be an update", l) is not None:
                    if re.search("rockstor.{}".format(arch), l) is not None:
                        new_version = l.strip().split()[3].split(":")[1]
            else:  # We are assuming openSUSE with dnf-yum output format
                # dnf-yum output line of interest; when presented:
                #  " rockstor   x86_64   3.9.2-51.2089   localrepo   15 M"
                if re.match(" rockstor", l) is not None:
                    new_version = l.strip().split()[2]
    return new_version


def update_run(subscription=None, update_all_other=False):
    # update_run modified to handle yum updates too
    # and avoid an ad hoc yum update function
    # If we have a yum update we don't stop/start Rockstor and
    # don't delete *.pyc files
    if subscription is not None:
        switch_repo(subscription)
    run_command([SYSTEMCTL, "start", "atd"])
    fh, npath = mkstemp()
    # Set system wide package manager refresh command according to distro.
    distro_id = distro.id()
    pkg_refresh_cmd = "{} --non-interactive refresh\n".format(ZYPPER)
    if distro_id == "rockstor":  # CentOS based Rockstor conditional
        pkg_refresh_cmd = "{} --setopt=timeout=600 -y update\n".format(YUM)
    # Set package manager rockstor install/update command according to distro.
    pkg_in_up_rockstor = "{} --non-interactive install rockstor\n".format(ZYPPER)
    if distro_id == "rockstor":  # CentOS based Rockstor conditional
        pkg_in_up_rockstor = "{} --setopt=timeout=600 -y install rockstor\n".format(YUM)
    pkg_update_all = ""
    if distro_id == "opensuse-leap":
        pkg_update_all = "{} --non-interactive update --no-recommends\n".format(ZYPPER)
    if distro_id == "opensuse-tumbleweed":
        pkg_update_all = "{} --non-interactive dist-upgrade --no-recommends\n".format(
            ZYPPER
        )
    with open(npath, "w") as atfo:
        if not update_all_other:
            atfo.write("sleep 10\n")
            atfo.write("{} stop rockstor\n".format(SYSTEMCTL))
            # rockstor-pre stop ensures initrock re-run on next rockstor start
            atfo.write("{} stop rockstor-pre\n".format(SYSTEMCTL))
            # Exclude eggs subdir, as these are in rpm so will be deleted
            # as otherwise floods YUM log with "No such file or directory"
            atfo.write(
                '/usr/bin/find {} -name "*.pyc" -not -path "*/eggs/*" -type f -delete\n'.format(
                    settings.ROOT_DIR
                )
            )
            atfo.write(pkg_refresh_cmd)
            # account for moving from dev/source to package install:
            atfo.write(pkg_in_up_rockstor)
            # the following rockstor start invokes rockstor-pre (initrock) also
            atfo.write("{} start rockstor\n".format(SYSTEMCTL))
        else:  # update_all_other True so update all bar the rockstor package.
            logger.info(
                "Updating all but rockstor package for distro {}".format(distro_id)
            )
            if distro_id == "rockstor":
                atfo.write("{} --setopt=timeout=600 -y -x rock* update\n".format(YUM))
            else:
                atfo.write("{} addlock rockstor\n".format(ZYPPER))
                atfo.write(pkg_update_all)
                atfo.write("{} removelock rockstor\n".format(ZYPPER))
        atfo.write("/bin/rm -f {}\n".format(npath))
    # out, err, rc = run_command([AT, '-f', npath, 'now + 1 minutes'])
    out, err, rc = run_command([AT, "-f", npath, "now"])
    time.sleep(120)
    return out, err, rc


def pkg_changelog(package, distro_id):
    """
    Takes a package name and builds a dictionary based on current and update
    info for that package by parsing the output from:
    yum changelog 1 package
    The result is formatted appropriate for display.
    :param package: A package name
    :param distro_id: System expected output from distro.id()
    :return: Dict indexed by 'name', 'installed', 'available' and 'description'
    """
    # we can't work with rpm -qi Build Date field: some packages have
    # Build Date > new package version changelog
    # pkg_changelog behaviour is output beautify too, returning pkg name,
    # changelog for installed package and available new package update
    # TODO: Find way to show pending update packages changelogs in openSUSE.
    #  could be pending addition to zypper via
    #  zypper info --changelog packagename
    #  https://github.com/openSUSE/zypper/issues/138
    out, err, rc = run_command([YUM, "changelog", "1", package], throw=False)
    package_info = {
        "name": package.split(".")[0],
        "installed": [],
        "available": [],
        "description": "",
    }
    if distro_id != "rockstor":
        package_info["available"] = [
            "Version and changelog of update not available in openSUSE"
        ]
    installed = False
    available = False
    for line in out:
        stripped_line = line.strip()
        if re.search("Available Packages", stripped_line) is not None:
            installed = False
            available = True
            continue
        if re.search("Installed Packages", stripped_line) is not None:
            installed = True
            continue
        if re.search("changelog stats", stripped_line) is not None:
            installed = False
            available = False
            break
        if installed and len(stripped_line) != 0:
            package_info["installed"].append(stripped_line)
        if available and len(stripped_line) != 0:
            package_info["available"].append(stripped_line)
    package_info["installed"] = "[line]".join(package_info["installed"])
    package_info["available"] = "[line]".join(package_info["available"])
    package_info["description"] = pkg_infos(package_info["name"], "DESCRIPTION")
    return package_info


def pkg_infos(package, tag="DESCRIPTION"):
    # Retrieve a package description and other infos  with some 'magic spells'
    # We query rpm dbs passing a queryformat, with default to DESCRIPTION
    # To @schakrava: this probably can help avoiding some reading loops used
    # to grab packages infos like on Rockstor updates check
    # Full ref for avail tags here: http://rpm.org/user_doc/query_format.html
    # and avail tags list with rpm --querytags
    tag = "%%{%s}" % tag
    out, err, rc = run_command([RPM, "-q", "--queryformat", tag, package], throw=False)
    if rc != 0:
        return ""
    return " ".join(out)


def pkg_update_check():
    """
    Retrieves list of available package updates and passes each in turn to
    pkg_changelog for package specific info and presentation formatting.
    :return: list of dictionaries returned by pkg_changelog()
    """
    # Query yum for updates and grab return code
    # yum check-update return code is 0 with no updates
    # and 100 if at least 1 update available.
    # But this is not the case with zypper equivalent.
    # Using -x rockstor* to avoid having Rockstor updated here
    # instead of Rockstor "ad hoc" updater
    distro_id = distro.id()
    if distro_id == "rockstor":
        # N.B. equivalent cmd - yum check-update -q -x 'rock*'
        # i.e. quotes important around wildcard
        pkg_list_all_other = [YUM, "check-update", "-q", "-x", "rock*"]
    else:
        # N.B. although we fail to exclude the rockstor package here, so it
        # will be listed, it is skipped in update_run(). Different behaviour
        # form before as will, re-trigger notification but workable for now.
        pkg_list_all_other = [ZYPPER, "--non-interactive", "-q", "list-updates"]
    out, err, rc = run_command(pkg_list_all_other, throw=False, log=True)
    if rc == 106:  # zypper specific
        logger.error("### REPOSITORY ERROR ###\n {}".format(err))
    packages = []
    # Read output skipping first one or two lines and last empty line
    # on every line we add changelog info and some beautify with pkg_changelog.
    if distro_id == "rockstor":
        for line in out[1:-1]:
            packages.append(pkg_changelog(line.split()[0].strip(), distro_id))
    else:
        # N.B. repo issues give warnings/info above the package updates table.
        for line in out:
            if line == "":
                continue
            if line[0] == "-" or line[0] == "S":
                continue
            # Skip "File 'repomd.xml' ..." and "Warning: ..." lines:
            line_fields = line.split()  # Assumed faster than re.match()
            if line_fields[0] == "File" or line_fields[0] == "Warning:":
                continue
            line_table_fields = line.split("|")
            if len(line_table_fields) < 3:
                continue  # Avoid index out of range on unknown line content.
            packages.append(pkg_changelog(line_table_fields[2].strip(), distro_id))
    return packages
