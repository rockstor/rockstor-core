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
import subprocess
import typing
from subprocess import run, CalledProcessError, TimeoutExpired
from time import sleep
from xml.etree.ElementTree import fromstring, ElementTree
from tempfile import mkstemp
from storageadmin.models import UpdateSubscription
from system.exceptions import CommandException
from system.osi import run_command
from system.services import systemctl
import shutil
import time
import requests
from django.conf import settings
import distro
import logging
import keyring
from keyring import set_password
from keyring.errors import KeyringError, PasswordSetError, KeyringLocked, NoKeyringError
from zypper_changelog_lib import get_zypper_changelog

logger = logging.getLogger(__name__)

RPM = "/usr/bin/rpm"
ZYPPER = "/usr/bin/zypper"
SYSTEMCTL = "/usr/bin/systemctl"
AT = "/usr/bin/at"
YCFILE = "/etc/yum/yum-cron.conf"  # Doesn't exist in openSUSE
STABLE_CREDENTIALS_FILE = "/etc/zypp/credentials.d/Rockstor-Stable"
# Zypper return codes:
ZYPPER_EXIT_ERR_INVALID_ARGS = 3  # Can occur when naming a non-existent repo.
ZYPPER_EXIT_ZYPP_LOCKED = 7  # Likely indicating a retry requirement.
ZYPPER_EXIT_INF_REPOS_SKIPPED = 106  # Likely not catastrophic and temporary.
# Zypper info return codes.
# These invoke subprocess.CalledProcessError with --xmlout but do not represent failure,
# rather a requirement to retrieve stdout from the exception, not the CompletedProcess.
zypp_info_codes = {
    100: "ZYPPER_EXIT_INF_UPDATE_NEEDED",
    101: "ZYPPER_EXIT_INF_SEC_UPDATE_NEEDED",
    102: "ZYPPER_EXIT_INF_REBOOT_NEEDED",
    103: "ZYPPER_EXIT_INF_RESTART_NEEDED",  # Associated with 'zypper needs-rebooting'.
    106: "ZYPPER_EXIT_INF_REPOS_SKIPPED",  # Likely not catastrophic and temporary.
}
zypp_err_codes = {
    1: "ZYPPER_EXIT_ERR_BUG",
    2: "ZYPPER_EXIT_ERR_SYNTAX",
    3: "ZYPPER_EXIT_ERR_INVALID_ARGS",  # Can occur when naming a non-existent repo.
    4: "ZYPPER_EXIT_ERR_ZYPP",
    5: "ZYPPER_EXIT_ERR_PRIVILEGES",
    6: "ZYPPER_EXIT_NO_REPOS",
    7: "ZYPPER_EXIT_ZYPP_LOCKED",  # Likely indicating a retry requirement.
    104: "ZYPPER_EXIT_INF_CAP_NOT_FOUND",  # Failure via insufficient capabilities.
    105: "ZYPPER_EXIT_ON_SIGNAL",  # Failure via cancellation i.e. OOM.
    107: "ZYPPER_EXIT_INF_RPM_SCRIPT_FAILED",  # Should be highlighted as an error.
}


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
    out, err, rc = run_command(
        [RPM, "-q", "--queryformat", tags, "rockstor"], throw=False
    )
    if rc != 0:  # Not installed is rc=1
        return "0.0.0-0", None
    date_list = []
    if get_build_date:
        try:
            # we get on second line: "Thu May 01 2025" we want 2025-May-01
            date_list = out[1].split()[1:]  # ["May",  "01",  "2025"]
        except Exception as e:
            logger.debug(
                f"failed to parse build date from 'rpm -qi rockstor`: {e.__str__}"
            )
            return out[0].strip(), None
        return out[0].strip(), f"{date_list[2]}-{date_list[0]}-{date_list[1]}"
    return out[0].strip(), None


def rpm_build_info(pkg: str) -> tuple[str, str | None]:
    version = "Unknown Version"
    date = None
    version, date = current_version(get_build_date=True)
    # Maintain compatibility with existing expectations for now.
    if version == "0.0.0-0":
        version = "Unknown Version"
    return version, date


def zypper_repos_list(max_wait: int = 1) -> typing.List[str]:
    """
    Simple wrapper for "zypper --xmlout lr Rockstor-Testing Rockstor-Stable".
    Retrieves a list of enabled Rockstor repositories.
    :return: list of enabled Rockstor repos by alias.
    """
    repo_list: typing.List[str] = []
    stdout_value: str | None = None
    try:
        zypp_run = run(
            ["zypper", "--xmlout", "lr", "Rockstor-Testing", "Rockstor-Stable"],
            capture_output=True,
            encoding="utf-8",  # stdout and stderr as string
            universal_newlines=True,
            timeout=max_wait,
            check=True,
        )
    except CalledProcessError as e:
        if e.returncode in zypp_info_codes.keys():
            logger.info(f"list repos returned {zypp_info_codes[e.returncode]}.")
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


def remove_rockstor_repo(
    repo_list: list[str] | None = None, max_wait: int = 1, retries: int = 2
) -> bool:
    """
    Retry wrapper for "zypper removerepo Rockstor-Testing Rockstor-Stable" by default.
    Retry on - "System management is locked by the application with pid ... (zypper).",
    indicated by ZYPPER_EXIT_ZYPP_LOCKED (return code 7)-
    Uses --xmlout to constrain output as we read only the return code.
    If one or more repo are not found, return code is still. 0.
    :param repo_list: List of repositories, default to all Rockstor-* repos.
    :param retries: Number of retries to attempt.
    :param max_wait: Max seconds expected for each execution.
    :return: Bool is zypper return code indicates a success.
    """
    if repo_list is None:
        repo_list = ["Rockstor-Testing", "Rockstor-Stable"]
    cmd_list = [
        "zypper",
        "--xmlout",
        "removerepo",
    ] + repo_list
    zypp_run = None
    for attempt in range(retries + 1):  # [0 1 2] for retries = 2
        try:
            zypp_run = run(
                cmd_list,
                capture_output=False,
                timeout=max_wait,
                check=True,
            )
        except CalledProcessError as e:
            if e.returncode in zypp_info_codes.keys():
                logger.info(f"Remove repo returned {zypp_info_codes[e.returncode]}.")
                return True
            if e.returncode != ZYPPER_EXIT_ZYPP_LOCKED:
                logger.error(f"Error removing Rockstor-* repositories: {e}")
                raise CommandException(cmd_list, e.stdout, e.stderr, e.returncode)
            if attempt <= retries:
                logger.info(f"--- Zypper locked: attempt {attempt +1}, retrying in 1s.")
                sleep(1)
                continue  # retry on zypper locked.
            raise CommandException(cmd_list, e.stdout, e.stderr, e.returncode)
        except TimeoutExpired as e:
            logger.error(f"Timeout removing repos (attempt {attempt + 1}): {e}")
            continue
    if not isinstance(zypp_run, subprocess.CompletedProcess):
        logger.error("Error removing old repositories.")
        return False
    return True


def update_zypp_auth_file(user, password):
    """
    Takes Appliance ID as username and Activation code as password and creates a zypper
    compatible Rockstor-Stable credentials file in /etc/zypp/credentials.d which is the
    default credentials.global.dir see: /etc/zypp/zypp.conf
    See also zypper-changelog-lib counterpart update_password_store().
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
    return True


def update_password_store(user, password):
    """
    Zypper-changelog-lib password-store counterpart, to update_zypp_auth_file().
    Takes Appliance ID as username and Activation code as password.
    Required to enable partial RPM pkg downloads for pending changelog retrieval.
    Employs python-keyring to update password-store keyring backend, already enabled
    for Rockstor Django secrets storage.
    :param user: Appliance ID
    :param password: Activation code
    :return: True if credentials file successfully created, or throws an exception.
    """
    # See conf/rockstor-pre.service for rockstor@localhost keyring setup.
    service = f"zypper-changelog-lib/Rockstor-Stable/"
    try:
        set_password(service_name=service, username=user, password=password)
    except NoKeyringError as e:
        logger.error(f"No rockstor@localhost keyring, try rebooting: {e.__str__()}")
    except KeyringLocked as e:
        logger.error(f"rockstor@localhost keyring locked: {e.__str__}")
    except PasswordSetError as e:
        logger.error(f"Web-UI changelog: Stable repo auth set issue. {e.__str__()}")
    except keyring.errors.KeyringError as e:
        logger.error(f"Unknown KeyringError: {e.__str__()}")
    return None


def switch_repo(subscription: UpdateSubscription, enable_repo: bool = True):
    logger.info(
        f"++ switch_repo({subscription.name}, enable_repo={enable_repo}) called."
    )
    repos_dir = "/etc/yum.repos.d"
    # Yum repo clean-up scheduled for removal post 5.1.0-0 Stable release.
    yum_file = "{}/Rockstor-{}.repo".format(repos_dir, subscription.name)
    if not enable_repo:
        logger.info("--- Removing all Rockstor-* repositories")
        if os.path.exists(yum_file):
            os.remove(yum_file)
        remove_rockstor_repo()
        return None
    repo_alias = "Rockstor-{}".format(subscription.name)
    rock_pub_key_file = "{}conf/ROCKSTOR-GPG-KEY".format(settings.ROOT_DIR)
    # Historically our base subscription url denotes our CentOS rpm repo.
    subscription_distro_url = subscription.url
    distro_id = distro.id()
    distro_version = distro.version()
    machine_arch = platform.machine()
    # Accommodate for distro 1.7.0 onwards reporting "opensuse" for id.
    if distro_id == "opensuse-leap" or distro_id == "opensuse":
        subscription_distro_url += "/leap/{}".format(distro_version)
    elif distro_id == "opensuse-tumbleweed" or distro_id == "opensuse-slowroll":
        subscription_distro_url += "/tumbleweed"
    # From Tumblweed/Slowroll 20250329-0 onwards remove all DNF/YUM use.
    current_repo_list = zypper_repos_list()
    # As from Leap15.4, update repositories are multi-arch. Maintain 15.3_aarch for now.
    if distro_version == "15.3" and machine_arch != "x86_64":
        subscription_distro_url += "_{}".format(machine_arch)
    if subscription.password is not None:
        repo_url = f"http://{subscription.appliance.uuid}@{subscription_distro_url}"
    else:
        repo_url = f"http://{subscription_distro_url}"
    logger.debug(f"REPO_URL={repo_url}")
    # Rockstor public key import call takes around 13 ms.
    run_command([RPM, "--import", rock_pub_key_file], log=True)
    if subscription.name == "Stable":
        # TODO: After 5.6.0-0 Stable this can be moved to after update_zypp_auth_file().
        # Required for now to update password-store on existing Stable systems.
        logger.info("Syncing password-store auth for Web-UI changelog feature.")
        update_password_store(subscription.appliance.uuid, subscription.password)
        if repo_alias not in current_repo_list:
            logger.info("++++ Enabling Stable as not in current repo list")
            if "Rockstor-Testing" in current_repo_list:
                logger.info("--- Testing enabled - removing repo")
                remove_rockstor_repo(["Rockstor-Testing"])
            update_zypp_auth_file(subscription.appliance.uuid, subscription.password)
            # If already added rc=4
            run_command(
                [
                    ZYPPER,
                    "--non-interactive",
                    "addrepo",
                    "--refresh",
                    f"{repo_url}?credentials={STABLE_CREDENTIALS_FILE}&auth=basic",
                    repo_alias,
                ],
                log=True,
                throw=False,
            )
        else:
            logger.info("*** Stable repo already enabled.")
    elif subscription.name == "Testing":
        if repo_alias not in current_repo_list:
            logger.info("++++ Enabling Testing as not in current repo list")
            if "Rockstor-Stable" in current_repo_list:
                logger.info("--- Stable enabled - removing repo")
                remove_rockstor_repo(["Rockstor-Stable"])
            # If already added rc=4
            run_command(
                [
                    ZYPPER,
                    "--non-interactive",
                    "addrepo",
                    "--refresh",
                    repo_url,
                    repo_alias,
                ],
                log=True,
                throw=False,
            )
        else:
            logger.info("*** Testing already enabled.")
    else:
        logger.info(f"The subscription name ({subscription.name}) is unknown.")
        # Possible 'Edge' release.
        return None
    return None


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
    Uses zypper-changelog-lib to see if an update
    to the 'rockstor' package is available, and if so, the current and updated
    versions are returned, along with the differential changelog.
    If there is no current (rpm) version, i.e. a source installation, the default
    changelog length for an available 'rockstor' rpm will be returned.
    :param subscription:
    :return:
    """
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
    if changelog_list:
        # First element is available package version pertaining to the changelog.
        new_version = changelog_list.pop(0)
    return version, new_version, changelog_list


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


def pkg_updates_info(max_wait: int = 15) -> typing.List[dict[str:str]]:
    """
    Fetch info on installable updates across all repos via zypper xml output call.
    Resolves as per 'zypper up' excluding packages with dependency problems.
    Adding `--all` includes packages with dependency problems.
    For "No updates found." [] is returned.
    Drop-in replacement for legacy pkg_update_check(), and its dependency of:
    pkg_changelog() (yum based), and its unique dependency of:
    pkg_infos()
    We don't retrieve non 'rockstor' package changelogs.
    Note: This procedure has no re-try capability as it is run, somewhat excessive,
    on every page refresh. This should be addressed in the planned front-end re-work.
    For now, the invocation has a hard-wired delay of a second to avoid locking
    zypper and blocking 'SYSTEM - Software update' invoking rockstor_pkg_update_check().
    """
    # Proposed output:
    # [ {'name': 'binutils', 'installed': '2.43-5.2', 'available': '2.43-6.1', 'description': 'C compiler ...'}, ...]
    logger.debug("pkg_updates_info() called")
    updates_info: typing.List[dict[str:str]] = []
    stdout_value: str | None = None
    zypp_run = None
    try:
        # rc = 1 when out = "package * is not installed"
        zypp_run = run(
            ["zypper", "--xmlout", "list-updates"],
            capture_output=True,
            encoding="utf-8",  # stdout and stderr as string
            universal_newlines=True,
            timeout=max_wait,
            check=True,
        )
    except CalledProcessError as e:
        if e.returncode in zypp_info_codes.keys():  # get stdout on zypper info codes.
            logger.info(f"list-updates returned {zypp_info_codes[e.returncode]}.")
            stdout_value = e.stdout
        elif e.returncode == ZYPPER_EXIT_ZYPP_LOCKED:
            logger.info(f"Skipped fetching updates, zypper busy.")
        else:
            if e.returncode in zypp_err_codes.keys():
                logger.error(f"list-updates returned {zypp_err_codes[e.returncode]}.")
            else:
                logger.error(f"Error fetching updates: {e}")
            return updates_info
    except TimeoutExpired as e:
        logger.error(f"Consider applying updates to reduce backlog: {e}")
        return updates_info
    if not stdout_value:
        if isinstance(zypp_run, subprocess.CompletedProcess):
            stdout_value = zypp_run.stdout
        else:
            return updates_info
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
            pkg_info["description"] = (
                "-- See: 'SYSTEM -> Software Update' to apply --.\n"
                + pkg_info["description"]
            )
        updates_info.append(pkg_info)
    return updates_info
