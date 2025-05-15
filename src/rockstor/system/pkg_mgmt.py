"""
Copyright (joint work) 2024 The Rockstor Project <https://rockstor.com>

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

import os
import platform
import re
import stat
import typing
from subprocess import run, CalledProcessError, TimeoutExpired
from xml.etree.ElementTree import fromstring, ElementTree
from tempfile import mkstemp
from storageadmin.models import UpdateSubscription
from system.osi import run_command
from system.services import systemctl
import shutil
import time
from datetime import datetime, timedelta
import requests
from django.conf import settings
from system.exceptions import CommandException
import distro
import logging

from zypper_changelog_lib import get_zypper_changelog

logger = logging.getLogger(__name__)

YUM = "/usr/bin/yum"
RPM = "/usr/bin/rpm"
ZYPPER = "/usr/bin/zypper"
SYSTEMCTL = "/usr/bin/systemctl"
AT = "/usr/bin/at"
YCFILE = "/etc/yum/yum-cron.conf"  # Doesn't exist in openSUSE
STABLE_CREDENTIALS_FILE = "/etc/zypp/credentials.d/Rockstor-Stable"
# Zypper return codes:
ZYPPER_EXIT_ERR_INVALID_ARGS = 3
ZYPPER_EXIT_ZYPP_LOCKED = 7


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


def current_version(get_build_date: bool = False) -> (str, str | None):
    """
    If the 'rockstor' package is installed, return a "version-release" string,
    otherwise return the flag version value of "0.0.0-0".
    If build_date is True, also return Build Date, otherwise return None.
    :param get_build_date: Boolean flag to request a build date look-up.
    :return: (version-release, build_date)
    """
    # https://rpm-software-management.github.io/rpm/manual/tags.html
    # from man rpm: ":day   Use strftime(3) "%a %b %d %Y" format.": Thu May 01 2025
    # Standardises output, or without :day we can get unix timestamp.
    # The following tags gives us a pre-formatted:
    # 'Version-Release' (first line)
    # 'Thu May 01 2025' (second line)
    tags = "%{VERSION}\-%{RELEASE}\\\n%{BUILDTIME:day}"
    out, err, rc = run_command([RPM, "-q", "--queryformat", tags, "rockstor"], throw=False)
    if rc != 0:  # Not installed is rc=1
        return "0.0.0-0", None
    date_list = []
    if get_build_date:
        try:
            # we get on second line: "Thu May 01 2025" we want 2025-May-01
            date_list = out[1].split()[1:]  # ["May",  "01",  "2025"]
        except Exception as e:
            logger.debug(f"failed to parse build date from 'rpm -qi rockstor`: {e.__str__}")
            return out[0].strip(), None
        return out[0].strip(), f"{date_list[2]}-{date_list[0]}-{date_list[1]}"
    return out[0].strip(), None


def rpm_build_info(pkg: str) -> tuple[str, str | None]:
    version = "Unknown Version"
    date = None
    # Non YUM/DNF path (rpm & zypper only)
    distro_id = distro.id()
    if distro_id == "opensuse-tumbleweed" or distro_id == "opensuse-slowroll":
        version, date = current_version(get_build_date=True)
        # Maintain compatibility with existing expectations for now.
        if version == "0.0.0-0":
            version = "Unknown Version"
        return version, date
    # Legacy YUM/DNF path: scheduled for deprecation/removal after 5.1.0-0
    try:
        o, e, rc = run_command([YUM, "info", "installed", "-v", pkg])
    except CommandException as e:
        # Catch "No matching Packages to list" so we can return:
        # ("Unknown Version", None)
        emsg = "Error: No matching Packages to list"
        # By checking both the first error element and the second to last we
        # catch one yum waiting for another to release yum lock.
        if e.err[0] == emsg or e.err[-2] == emsg:
            logger.info('No "{}" package found: source install?'.format(pkg))
            return version, date
        # otherwise, we raise an exception as normal.
        raise e
    for line in o:
        if re.match("Buildtime", line) is not None:
            # earlier openSUSE Rockstor (using dnf-yum):
            #     "Buildtime    : Fri 29 Nov 2019 18:34:43 GMT"
            # opensuse-tumblweed | opensuse-slowroll Rockstor (using dnf-yum):
            #     "Buildtime    : Fri 07 Mar 2025 08:16:20 AM WET"
            # we return 2017-Dec-06 | 2019-Nov-30 | 2025-Mar-08 respectively.
            # Note the plus-one day on from retrieved Build time with zero padding.
            dfields = line.strip().split()
            # Assuming we are openSUSE variant and so using dnf-yum
            dstr = dfields[5] + " " + dfields[4] + " " + dfields[3]
            bdate = datetime.strptime(dstr, "%Y %b %d")
            bdate += timedelta(days=1)
            date = bdate.strftime("%Y-%b-%d")
        if re.match("Version ", line) is not None:
            version = line.strip().split()[2]
        if re.match("Release ", line) is not None:
            version = "{}-{}".format(version, line.strip().split()[2])
    return version, date


def zypper_repos_list_legacy():
    """
    Low level wrapper around "zypper repos"
    :return: List of repo Alias's
    """
    # Superseeded by zypper_repos_list() scheduled for deprecation/removal after 5.1.0-0
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


def zypper_repos_list(max_wait: int = 1) -> typing.List[str]:
    """
    Simple wrapper for "zypper -x lr Rockstor-Testing Rockstor-Stable".
    Retrieves a list of enabled Rockstor repositories.
    :return: list of enabled Rockstor repos by alias.
    """
    repo_list: typing.List[str] = []
    stdout_value: str | None = None
    try:
        zypp_run = run(
            ["zypper", "-x", "lr", "Rockstor-Testing", "Rockstor-Stable"],
            capture_output=True,
            encoding="utf-8",  # stdout and stderr as string
            universal_newlines=True,
            timeout=max_wait,
            check=True,
        )
    except CalledProcessError as e:
        if e.returncode != ZYPPER_EXIT_ERR_INVALID_ARGS:
            logger.error(f"{e.stdout}Error fetching repository list: ({e})")
            return []
        stdout_value = e.stdout
    except TimeoutExpired as e:
        logger.error(f"Package system may be busy: {e}")
        return []
    if not stdout_value:
        logger.info(f"Both Testing and Stable were inadvertently enabled")
        stdout_value = zypp_run.stdout
    repo_tree = ElementTree(fromstring(stdout_value))
    repo_root = repo_tree.getroot()
    for repo in repo_root.iter("repo"):
        if repo.get("enabled") == "1":
            repo_list.append(repo.get("alias"))
    return repo_list


def create_credentials_file(user, password):
    """
    Takes Appliance ID as username and Activation code as password and creates a zypper
    compatible Rockstor-Stable credentials file in /etc/zypp/credentials.d which is the
    default credentials.global.dir see: /etc/zypp/zypp.conf
    :param user: Appliance ID
    :param password: Activation code
    :return: True if credentials file successfully created, or throws an exception.
    """
    # Create a temp file to construct our proposed Rockstor-Stable file prior to copying
    # with preserved attributes.
    tfo, npath = mkstemp()
    # Pythons _candidate_tempdir_list() should ensure our npath temp file is
    # in memory (tmpfs). From https://docs.python.org/2/library/tempfile.html
    # we have "Creates a temporary file in the most secure manner possible."
    try:
        with open(npath, "w") as temp_file:
            temp_file.write("username={}\n".format(user))
            temp_file.write("password={}\n".format(password))
        # shutil.copy2 is equivalent to cp -p (preserver attributes).
        # This preserves the secure defaults of the temp file without having
        # to chmod thereafter. Result is the desired:
        # -rw------- 1 root root
        # ie rw to root only or 0600
        # and avoiding a window prior to a separate chmod command.
        shutil.copy2(npath, STABLE_CREDENTIALS_FILE)
    except Exception as e:
        msg = "Exception while creating {}: {}".format(
            STABLE_CREDENTIALS_FILE, e.__str__()
        )
        raise Exception(msg)
    finally:
        if os.path.exists(npath):
            try:
                os.remove(npath)
            except Exception as e:
                msg = "Exception while removing temp file {}: {}".format(
                    npath, e.__str__()
                )
                raise Exception(msg)
    # TODO Stash/Sync credentials in our password-store also, i.e. via python-keyring.
    #  This enables their use in zypper-changelog-lib or Stable Updates repo.
    return True


def switch_repo(subscription, on=True):
    repos_dir = "/etc/yum.repos.d"
    yum_file = "{}/Rockstor-{}.repo".format(repos_dir, subscription.name)
    rock_pub_key_file = "{}conf/ROCKSTOR-GPG-KEY".format(settings.ROOT_DIR)
    # Historically our base subscription url denotes our CentOS rpm repo.
    subscription_distro_url = subscription.url
    distro_id = distro.id()
    distro_version = distro.version()
    machine_arch = platform.machine()
    use_zypper: bool = True
    yum_also: bool = True  # Leap and before use yum for changelog function.
    repo_alias = "Rockstor-{}".format(subscription.name)
    logger.debug("########### SWITCH REPO repo-alias = {}".format(repo_alias))
    # Accommodate for distro 1.7.0 onwards reporting "opensuse" for id.
    if distro_id == "opensuse-leap" or distro_id == "opensuse":
        subscription_distro_url += "/leap/{}".format(distro_version)
    elif distro_id == "opensuse-tumbleweed" or distro_id == "opensuse-slowroll":
        subscription_distro_url += "/tumbleweed"
        # Tumblweed/Slowroll from 20250329-0 onwards uses zypper-changelog-plugin
        yum_also = False
    else:
        use_zypper = False
    # As from Leap15.4, update repositories are multi-arch. Maintain 15.3_aarch for now.
    if distro_version == "15.3" and machine_arch != "x86_64":
        subscription_distro_url += "_{}".format(machine_arch)
    # Check if dir /etc/yum.repos.d exists, if not create it: but only on non-TW/Slowroll
    if yum_also and not os.path.isdir(repos_dir):
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
                create_credentials_file(
                    subscription.appliance.uuid, subscription.password
                )
                run_command(
                    [
                        ZYPPER,
                        "--non-interactive",
                        "addrepo",
                        "--refresh",
                        "http://{}@{}?credentials={}&auth=basic".format(
                            subscription.appliance.uuid,
                            subscription_distro_url,
                            STABLE_CREDENTIALS_FILE,
                        ),
                        repo_alias,
                    ],
                    log=True,
                    throw=False,
                )
            # TODO: Avoid re-calling zypper_repos_list(), we already have zypper_repos_list()
            #  we just need to know if a re-call is required from our own actions.
            if subscription.name == "Testing" and repo_alias not in zypper_repos_list():
                if "Rockstor-Stable" in current_repo_list:
                    run_command([ZYPPER, "removerepo", "Rockstor-Stable"])
                # If already added rc=4
                run_command(
                    [ZYPPER, "addrepo", "--refresh", repo_url, repo_alias],
                    log=True,
                    throw=False,
                )
        # N.B. on Leap we also use YUM (read only) to retrieve changelogs
        if yum_also:
            with open(yum_file, "w") as rfo:
                rfo.write("[Rockstor-{}]\n".format(subscription.name))
                rfo.write("name={}\n".format(subscription.description))
                rfo.write("baseurl={}\n".format(repo_url))
                rfo.write("enabled=1\n")
                rfo.write("gpgcheck=1\n")
                rfo.write("gpgkey=file://{}\n".format(rock_pub_key_file))
                rfo.write("metadata_expire=1h\n")
                rfo.write("exclude=*.src\n")  # src changelogs = false positive update flag.
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
            timeout=10,
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


def rockstor_pkg_update_check(
    subscription: None | UpdateSubscription = None,
) -> (str, str, list[str]):
    """
    For Slowroll/Tumbleweed zypper-changelog-lib is used to ascertain if an update
    to the 'rockstor' package is available, and if so, the current and updated
    versions are returned, along with the differential changelog.
    If there is no current (rpm) version, i.e. a source installation, the default
    changelog length for an available 'rockstor' rpm will be returned.
    :param subscription:
    :return:
    """
    distro_id = distro.id()
    machine_arch = platform.machine()
    if subscription is not None:
        switch_repo(subscription)
    pkg = f"rockstor*{machine_arch}"
    rpm_installed: bool = False  # Until we find otherwise
    version, date = rpm_build_info(pkg)
    if date is not None:
        rpm_installed = True
    new_version = None
    updates = []
    # RPM & zypper only path
    if distro_id == "opensuse-tumbleweed" or distro_id == "opensuse-slowroll":
        # Retrieve changelog via zypper-changelog-lib
        if subscription is None:
            return version, version, updates
        # Rockstor's Repo alias is either "Rockstor-Testing" or "Rockstor-Stable".
        zyppchange = get_zypper_changelog(
            pkg_list=["rockstor"],
            repo_list=[f"Rockstor-{subscription.name}"],
            only_updates=rpm_installed,
        )
        if zyppchange is None:
            logger.debug("get_zypper_changelog() returned None.")
            return version, version, updates
        changelog_list: list = zyppchange.get("rockstor", [])
        if (
            changelog_list
        ):  # First element is available package version pertaining to the changelog.
            new_version = changelog_list.pop(0)
        return version, new_version, changelog_list
    # Legacy YUM/DNF path: scheduled for deprecation/removal after 5.1.0-0
    if date is None:
        # None date signifies no rpm installed so list all changelog entries.
        date = "all"
    log = False
    available = False
    # We are assuming openSUSE with dnf-yum specific options
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
    for line in o:
        # We have possible targets of:
        # "Listing changelogs since 2019-11-29" - legacy yum and dnf-yum
        # "Listing all changelogs" - legacy yum and dnf-yum with no --count=#
        # "Listing # latest changelogs" - dnf-yum with a --count=# options
        if re.match("Listing", line) is not None:
            available = True
        if not available:
            continue
        if new_version is None:
            if re.match("rockstor-", line) is not None:  # legacy yum
                # eg: "rockstor-3.9.2-51.2089.x86_64"
                new_version = (
                    line.split()[0]
                    .split("rockstor-")[1]
                    .split(".{}".format(machine_arch))[0]
                )
            if re.match("Changelogs for rockstor-", line) is not None:  # dnf-yum
                # eg: "Changelogs for rockstor-3.9.2-51.2089.x86_64"
                new_version = (
                    line.split()[2]
                    .split("rockstor-")[1]
                    .split(".{}".format(machine_arch))[0]
                )
        if log is True:
            updates.append(line)
            if len(line.strip()) == 0:
                log = False
        if re.match("\* ", line) is not None:
            updates.append(line)
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
    the latest version available from "Version" column
    :return:
    """
    new_version = None
    # TODO: We might use "zypper se -s --match-exact rockstor" and parse first
    #  line with rockstor in second column but unit test will be defunct.
    #  Advantage: works with no rockstor version installed, no so dnf-yum
    # Add quite & XML output: zypper --quiet --xmlout se -s --match-exact rockstor
    # Maybe https://github.com/martinblech/xmltodict via pip install xmltodict
    # Or
    o, e, rc = run_command([YUM, "update", pkg_name, "--assumeno"], throw=False)
    if rc == 1:
        for line in o:
            # We are assuming openSUSE with dnf-yum output format
            # dnf-yum output line of interest; when presented:
            #  " rockstor   x86_64   3.9.2-51.2089   localrepo   15 M"
            if re.match(" rockstor", line) is not None:
                new_version = line.strip().split()[2]
    return new_version


def update_run(subscription=None, update_all_other=False):
    if subscription is not None:
        switch_repo(subscription)
    run_command([SYSTEMCTL, "start", "atd"])
    fh, npath = mkstemp()
    # Set system-wide package manager refresh command according to distro.
    distro_id = distro.id()
    pkg_refresh_cmd = "{} --non-interactive refresh\n".format(ZYPPER)
    # Set package manager rockstor install/update command according to distro.
    pkg_in_up_rockstor = "{} --non-interactive install rockstor\n".format(ZYPPER)
    pkg_update_all = ""
    # Accommodate for distro 1.7.0 onwards reporting "opensuse" for id.
    if distro_id == "opensuse-leap" or distro_id == "opensuse":
        pkg_update_all = "{} --non-interactive update --no-recommends\n".format(ZYPPER)
    if distro_id == "opensuse-tumbleweed" or distro_id == "opensuse-slowroll":
        pkg_update_all = "{} --non-interactive dist-upgrade --no-recommends\n".format(
            ZYPPER
        )
    with open(npath, "w") as atfo:
        if not update_all_other:
            atfo.write("sleep 10\n")
            atfo.write(pkg_refresh_cmd)
            # Unset inherited VIRTUAL_ENV environmental variable before invoking rpm/zypper
            atfo.write("unset VIRTUAL_ENV\n")
            atfo.write(pkg_in_up_rockstor)
            # rockstor-bootstrap Requires rockstor which Requires rockstor-pre (initrock) which Requires rockstor-build
            atfo.write("{} start rockstor-bootstrap\n".format(SYSTEMCTL))
        else:  # update_all_other True so update all bar the rockstor package.
            logger.info(
                "Updating all but rockstor package for distro {}".format(distro_id)
            )
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
    N.B. to be superseded by pkg_updates_info()
    Takes a package name and builds a dictionary based on current and update
    info for that package by parsing the output from:
    yum changelog 1 package
    The result is formatted appropriate for display.

    :param package: A package name
    :param distro_id: System expected output from distro.id()
    :return: Dict indexed by 'name', 'installed', 'available' and 'description'
    """
    # Legacy YUM/DNF path: scheduled for deprecation/removal after 5.1.0-0
    # we can't work with rpm -qi Build Date field: some packages have
    # Build Date > new package version changelog
    # pkg_changelog behaviour is output beautify too, returning pkg name,
    # changelog for installed package and available new package update
    # We now use zypper-changelog-lib for pending 'rockstor' pkg changelogs.
    #  could be pending addition to zypper via
    #  zypper info --changelog packagename
    #  https://github.com/openSUSE/zypper/issues/138
    out, err, rc = run_command([YUM, "changelog", "1", package], throw=False)
    package_info = {
        "name": package.split(".")[0],
        "installed": "",
        "available": "",
        "description": "",
    }
    # We don't retrieve non 'rockstor' package changelogs.
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
    # N.B. to be superseded by pkg_updates_info()
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
    N.B. to be superseded by pkg_updates_info()
    :return: list of dictionaries returned by pkg_changelog()
    """
    distro_id = distro.id()
    if distro_id == "opensuse-tumbleweed" or distro_id == "opensuse-slowroll":
        return pkg_updates_info()
    # Legacy YUM/DNF path: scheduled for deprecation/removal after 5.1.0-0
    # Query yum for updates and grab return code
    # yum check-update return code is 0 with no updates
    # and 100 if at least 1 update available.
    # But this is not the case with zypper equivalent.
    # Using -x rockstor* to avoid having Rockstor updated here
    # instead of Rockstor "ad hoc" updater
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


def pkg_updates_info(max_wait: int = 14) -> typing.List[dict[str : str]]:
    """
    Fetch info on installable updates across all repos via zypper xml output call.
    Resolves as per 'zypper up' excluding packages with dependency problems.
    Adding `--all` includes packages with dependency problems.
    For "No updates found." [] is returned.
    Intended as a drop-in replacement for pkg_update_check(), and its dependency of:
    pkg_changelog() (yum based), and its unique dependency of:
    pkg_infos()
    We don't retrieve non 'rockstor' package changelogs.
    """
    # Proposed output:
    # [ {'name': 'binutils', available': '2.43-6.1', 'installed': '2.43-5.2', 'description': 'C compiler ...'}, ...]
    updates_info: typing.List[dict[str : str]] = []
    try:
        # rc = 1 when out = "package * is not installed"
        zypp_run = run(
            ["zypper", "-x", "--non-interactive", "list-updates"],
            capture_output=True,
            encoding="utf-8",  # stdout and stderr as string
            universal_newlines=True,
            timeout=max_wait,
            check=True,
        )
    except CalledProcessError as e:
        logger.error(f"Error fetching updates: {e}")
        return updates_info
    except TimeoutExpired as e:
        logger.error(f"Consider applying updates to reduce backlog: {e}")
        return updates_info
    stdout_value = zypp_run.stdout
    # logger.info(f"PKG_UPDATES_info() stdout={stdout_value}")
    updates_tree = ElementTree(fromstring(stdout_value))
    updates_root = updates_tree.getroot()
    for update in updates_root.iter("update"):
        pkg_info: dict = {
            "name": update.get("name"),
            "installed": update.get("edition-old"),
            "available": update.get("edition"),
            "description": update.find("description").text,
            # "summary": update.find("summary").text,
            # "repo_alias": update.find("source").get("alias")
        }
        if pkg_info["name"] == "rockstor":
            continue
        updates_info.append(pkg_info)
    return updates_info
