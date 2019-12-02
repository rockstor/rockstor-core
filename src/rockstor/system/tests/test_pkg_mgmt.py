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
import unittest
from mock import patch

from system.pkg_mgmt import (
    pkg_update_check,
    pkg_changelog,
    zypper_repos_list,
    rpm_build_info,
    pkg_latest_available,
)


class SystemPackageTests(unittest.TestCase):
    """
    The tests in this suite can be run via the following command:
    cd <root dir of rockstor ie /opt/rockstor-dev>
    ./bin/test --settings=test-settings -v 3 -p test_pkg_mgmt*
    """

    def setUp(self):
        self.patch_run_command = patch("system.pkg_mgmt.run_command")
        self.mock_run_command = self.patch_run_command.start()

        # We need to test the conditions of distro.id() returning one of:
        # rockstor, opensuse-leap, opensuse-tumbleweed
        self.patch_distro = patch("system.pkg_mgmt.distro")
        self.mock_distro = self.patch_distro.start()

        # Mock pkg_infos to return "" to simplify higher level testing.
        self.patch_pkg_infos = patch("system.pkg_mgmt.pkg_infos")
        self.mock_pkg_infos = self.patch_pkg_infos.start()
        self.mock_pkg_infos.return_value = ""

    def tearDown(self):
        patch.stopall()

    def test_pkg_changelog(self):
        """
        Test pkg_changelog, a package changelog (including update changes)
        parser and presenter
        :return:
        """
        # Example output form "yum changelog 1 sos.noarch" such as is executed
        # in pkg_changelog()
        out = [
            [
                "==================== Installed Packages ====================",  # noqa E501
                "sos-3.6-17.el7.centos.noarch             installed",  # noqa E501
                "* Tue Apr 23 05:00:00 2019 CentOS Sources <bugs@centos.org> - 3.6-17.el7.centos",  # noqa E501
                "- Roll in CentOS Branding",  # noqa E501
                ""  # noqa E501
                "==================== Available Packages ====================",  # noqa E501
                "sos-3.7-6.el7.centos.noarch              updates",  # noqa E501
                "* Tue Sep  3 05:00:00 2019 CentOS Sources <bugs@centos.org> - 3.7-6.el7.centos",  # noqa E501
                "- Roll in CentOS Branding",  # noqa E501
                "",  # noqa E501
                "changelog stats. 2 pkgs, 2 source pkgs, 2 changelogs",  # noqa E501
                "",  # noqa E501
            ]
        ]
        err = [[""]]
        rc = [0]
        expected_results = [
            {
                "available": "sos-3.7-6.el7.centos.noarch              updates[line]* Tue Sep  3 05:00:00 2019 CentOS Sources <bugs@centos.org> - 3.7-6.el7.centos[line]- Roll in CentOS Branding",  # noqa E501
                "description": "",
                "name": "fake",
                "installed": "sos-3.6-17.el7.centos.noarch             installed[line]* Tue Apr 23 05:00:00 2019 CentOS Sources <bugs@centos.org> - 3.6-17.el7.centos[line]- Roll in CentOS Branding",  # noqa E501
            }
        ]
        distro_id = ["rockstor"]
        #
        # TODO: add openSUSE Leap example output. But currently exactly the same
        #  command but no available is listed as yum knows only rockstor repos.
        #
        for o, e, r, expected, distro in zip(out, err, rc, expected_results, distro_id):
            self.mock_run_command.return_value = (o, e, r)
            returned = pkg_changelog("fake.123", distro)
            self.assertEqual(
                returned,
                expected,
                msg="Un-expected pkg_changelog() result:\n "
                "returned = ({}).\n "
                "expected = ({}).".format(returned, expected),
            )

    def test_pkg_update_check(self):
        """
        Test pkg_update_check() across distro.id values and consequently different
        output format of:
        distro.id = "rockstor" (CentOS) base
        yum check-update -q -x rock*
        and:
        output format of:
        distro.id = "opensuse-leap"
        zypper -q list-updates
        and:
        distro.id = "opensuse-tumbleweed"
        same command as for opensuse-leap
        """
        # Mock pkg_changelog to allow for isolated testing of yum_check
        self.patch_pkg_changelog = patch("system.pkg_mgmt.pkg_changelog")
        self.mock_pkg_changelog = self.patch_pkg_changelog.start()

        def fake_pkg_changelog(*args, **kwargs):
            """
            Stubbed out fake pkg_changelog to allow for isolation of caller
            N.B. currenlty only uses single package test data to simply dict
            comparisons, ie recersive dict sort othewise required.
            :param args:  
            :param kwargs:
            :return: Dict indexed by name=arg[0], installed, available, and description.
            last 3 are = [] unless arg[1] is not "rockstor" then available has different
            content.
            """
            pkg_info = {"name": args[0].split(".")[0]}
            pkg_info["installed"] = ""
            pkg_info["available"] = ""
            if args[1] != "rockstor":
                pkg_info[
                    "available"
                ] = "Version and changelog of update not available in openSUSE"
            pkg_info["description"] = ""
            return pkg_info

        self.mock_pkg_changelog.side_effect = fake_pkg_changelog

        # TODO: We need more example here of un-happy paths
        # zypper spaces in Repository name Example,
        out = [
            [
                "S | Repository             | Name                    | Current Version                       | Available Version                     | Arch  ",  # noqa E501
                "--+------------------------+-------------------------+---------------------------------------+---------------------------------------+-------",  # noqa E501
                "v | Main Update Repository | aaa_base                | 84.87+git20180409.04c9dae-lp151.5.3.1 | 84.87+git20180409.04c9dae-lp151.5.6.1 | x86_64",  # noqa E501
                "",
            ]
        ]
        expected_result = [
            [
                {
                    "available": "Version and changelog of update not available in openSUSE",
                    "description": "",
                    "name": "aaa_base",
                    "installed": "",
                }
            ]
        ]
        err = [[""]]
        rc = [0]
        dist_id = ["opensuse-tumbleweed"]
        #
        # zypper no spaces in Repository name Example,
        # actual Leap 15.0 but no-space repos also seen in other openSUSE variants.
        out.append(
            [
                "S | Repository                | Name                            | Current Version                             | Available Version                           | Arch",  # noqa E501
                "--+---------------------------+---------------------------------+---------------------------------------------+---------------------------------------------+-------",  # noqa E501
                "v | openSUSE-Leap-15.0-Update | NetworkManager                  | 1.10.6-lp150.4.6.1                          | 1.10.6-lp150.4.9.1                          | x86_64",  # noqa E501
                "",
            ]
        )
        expected_result.append(
            [
                {
                    "available": "Version and changelog of update not available in openSUSE",
                    "description": "",
                    "name": "NetworkManager",
                    "installed": "",
                }
            ]
        )
        err.append([""])
        rc.append(0)
        dist_id.append("opensuse-tumbleweed")
        #
        # CentOS yum output example, ie one clear line above.
        out.append(
            [
                "",
                "epel-release.noarch                                                                        7-12                                                                        epel",  # noqa E501
                "",
            ]
        )
        expected_result.append(
            [
                {
                    "available": "",
                    "description": "",
                    "name": "epel-release",
                    "installed": "",
                }
            ]
        )
        err.append([""])
        rc.append(100)
        dist_id.append("rockstor")
        #
        # When we have a poorly repo.
        #     '/usr/bin/zypper', '--non-interactive', '-q', 'list-updates']
        out.append(
            [
                "",
                "",
                "",
                "",
                "File 'repomd.xml' from repository 'Rockstor-Testing' is unsigned, continue? [yes/no] (no): no",  # noqa E501
                "Warning: Skipping repository 'Rockstor-Testing' because of the above error.",  # noqa E501
                "S | Repository             | Name                    | Current Version                       | Available Version                     | Arch  ",  # noqa E501
                "--+------------------------+-------------------------+---------------------------------------+---------------------------------------+-------",  # noqa E501
                "v | Main Update Repository | aaa_base                | 84.87+git20180409.04c9dae-lp151.5.3.1 | 84.87+git20180409.04c9dae-lp151.5.9.1 | x86_64",  # noqa E501
                "v | Main Update Repository | aaa_base-extras         | 84.87+git20180409.04c9dae-lp151.5.3.1 | 84.87+git20180409.04c9dae-lp151.5.9.1 | x86_64",  # noqa E501
                "v | Main Update Repository | apparmor-parser         | 2.12.2-lp151.3.2                      | 2.12.3-lp151.4.3.1                    | x86_64",  # noqa E501
                "v | Main Update Repository | bash                    | 4.4-lp151.9.53                        | 4.4-lp151.10.3.1                      | x86_64",  # noqa E501
                "",
            ]
        )
        expected_result.append(
            [
                {
                    "available": "Version and changelog of update not available in openSUSE",
                    "description": "",
                    "name": "aaa_base",
                    "installed": "",
                },
                {
                    "available": "Version and changelog of update not available in openSUSE",
                    "description": "",
                    "name": "aaa_base-extras",
                    "installed": "",
                },
                {
                    "available": "Version and changelog of update not available in openSUSE",
                    "description": "",
                    "name": "apparmor-parser",
                    "installed": "",
                },
                {
                    "available": "Version and changelog of update not available in openSUSE",
                    "description": "",
                    "name": "bash",
                    "installed": "",
                },
            ]
        )
        err.append(
            [
                "Repository 'Rockstor-Testing' is invalid.",
                "[Rockstor-Testing|http://updates.rockstor.com:8999/rockstor-testing/leap/15.1] Valid metadata not found at specified URL",  # noqa E501
                "Some of the repositories have not been refreshed because of an error.",  # noqa E501
                "",
            ]
        )
        rc.append(106)
        dist_id.append("opensuse-leap")
        #
        for o, e, r, expected, distro in zip(out, err, rc, expected_result, dist_id):
            self.mock_run_command.return_value = (o, e, r)
            self.mock_distro.id.return_value = distro
            returned = pkg_update_check()
            self.assertEqual(
                returned,
                expected,
                msg="Un-expected yum_check() result:\n "
                "returned = ({}).\n "
                "expected = ({}).".format(returned, expected),
            )

    def test_zypper_repos_list(self):
        # Test empty return values
        out = [[""]]
        err = [[""]]
        rc = [0]
        expected_results = [[]]
        # test typical output
        out.append(
            [
                "",
                "#  | Alias                     | Name                               | Enabled | GPG Check | Refresh",  # noqa E501
                "---+---------------------------+------------------------------------+---------+-----------+--------",  # noqa E501
                " 1 | Local-Repository          | Local-Repository                   | Yes     | ( p) Yes  | Yes    ",  # noqa E501
                " 2 | Rockstor-Testing          | Rockstor-Testing                   | Yes     | ( p) Yes  | Yes    ",  # noqa E501
                " 3 | illuusio                  | illuusio                           | Yes     | (r ) Yes  | Yes    ",  # noqa E501
                " 4 | repo-debug                | Debug Repository                   | No      | ----      | ----   ",  # noqa E501
                " 5 | repo-debug-non-oss        | Debug Repository (Non-OSS)         | No      | ----      | ----   ",  # noqa E501
                " 6 | repo-debug-update         | Update Repository (Debug)          | No      | ----      | ----   ",  # noqa E501
                " 7 | repo-debug-update-non-oss | Update Repository (Debug, Non-OSS) | No      | ----      | ----   ",  # noqa E501
                " 8 | repo-non-oss              | Non-OSS Repository                 | Yes     | (r ) Yes  | No     ",  # noqa E501
                " 9 | repo-oss                  | Main Repository                    | Yes     | (r ) Yes  | No     ",  # noqa E501
                "10 | repo-source               | Source Repository                  | No      | ----      | ----   ",  # noqa E501
                "11 | repo-source-non-oss       | Source Repository (Non-OSS)        | No      | ----      | ----   ",  # noqa E501
                "12 | repo-update               | Main Update Repository             | Yes     | (r ) Yes  | No     ",  # noqa E501
                "13 | repo-update-non-oss       | Update Repository (Non-Oss)        | Yes     | (r ) Yes  | No     ",  # noqa E501
                "",
            ]
        )
        err.append([""])
        rc.append(0)
        expected_results.append(
            [
                "Local-Repository",
                "Rockstor-Testing",
                "illuusio",
                "repo-debug",
                "repo-debug-non-oss",
                "repo-debug-update",
                "repo-debug-update-non-oss",
                "repo-non-oss",
                "repo-oss",
                "repo-source",
                "repo-source-non-oss",
                "repo-update",
                "repo-update-non-oss",
            ]
        )

        for o, e, r, expected in zip(out, err, rc, expected_results):
            self.mock_run_command.return_value = (o, e, r)
            returned = zypper_repos_list()
            self.assertEqual(
                returned,
                expected,
                msg="Un-expected zypper_repos_list() result:\n "
                "returned = ({}).\n "
                "expected = ({}).".format(returned, expected),
            )

    def test_rpm_build_info(self):
        """
        rpm_build_info strips out and concatenates Version and Release info for the
        rockstor package. This is returned along with a standardised date format for
        the Buildtime which is also parse out. N.B. the build time has 1 day added
        to it for historical reasons.
        """
        # legacy rockstor/CentOS YUM:
        dist_id = ["rockstor"]
        out = [
            [
                'Loading "changelog" plugin',
                'Loading "fastestmirror" plugin',
                "Config time: 0.010",
                "Yum version: 3.4.3",
                "rpmdb time: 0.000",
                "Installed Packages",
                "Name        : rockstor",
                "Arch        : x86_64",
                "Version     : 3.9.2",
                "Release     : 50.2093",
                "Size        : 85 M",
                "Repo        : installed",
                "From repo   : localrepo",
                "Committer   : Philip Guyton <philip@yewtreeapps.com>",
                "Committime  : Wed Nov 13 04:00:00 2019",
                "Buildtime   : Fri Nov 29 14:03:17 2019",
                "Install time: Sun Dec  1 07:23:38 2019",
                "Installed by: root <root>",
                "Changed by  : System <unset>",
                "Summary     : Btrfs Network Attached Storage (NAS) Appliance.",
                "URL         : http://rockstor.com/",
                "License     : GPL",
                "Description : Software raid, snapshot capable NAS solution with built-in file",
                "            : integrity protection. Allows for file sharing between network",
                "            : attached devices.",
                "",
                "",
            ]
        ]
        err = [[""]]
        rc = [0]
        expected_results = [("3.9.2-50.2093", "2019-Nov-30")]
        # Leap15.1 dnf-yum
        dist_id.append("opensuse-leap")
        out.append(
            [
                "Loaded plugins: builddep, changelog, config-manager, copr, debug, debuginfo-install, download, generate_completion_cache, needs-restarting, playground, repoclosure, repodiff, repograph, repomanage, reposync",  # noqa E501
                "DNF version: 4.2.6",
                "cachedir: /var/cache/dnf",
                "Waiting for process with pid 30565 to finish.",
                "No module defaults found",
                "Installed Packages",
                "Name         : rockstor",
                "Version      : 3.9.2",
                "Release      : 50.2093",
                "Architecture : x86_64",
                "Size         : 82 M",
                "Source       : rockstor-3.9.2-50.2093.src.rpm",
                "Repository   : @System",
                "Packager     : None",
                "Buildtime    : Sat 30 Nov 2019 11:50:41 AM GMT",
                "Install time : Sun 01 Dec 2019 03:23:03 PM GMT",
                "Summary      : Btrfs Network Attached Storage (NAS) Appliance.",
                "URL          : http://rockstor.com/",
                "License      : GPL",
                "Description  : Software raid, snapshot capable NAS solution with built-in file",
                "             : integrity protection. Allows for file sharing between network",
                "             : attached devices.",
                "",
                "",
            ]
        )
        err.append([""])
        rc.append(0)
        expected_results.append(("3.9.2-50.2093", "2019-Dec-01"))
        # Tumbleweed dnf-yum
        dist_id.append("opensuse-tumbleweed")
        out.append(
            [
                "Loaded plugins: builddep, changelog, config-manager, copr, debug, debuginfo-install, download, generate_completion_cache, needs-restarting, playground, repoclosure, repodiff, repograph, repomanage, reposync",  # noqa E501
                "DNF version: 4.2.6",
                "cachedir: /var/cache/dnf",
                "No module defaults found",
                "Installed Packages",
                "Name         : rockstor",
                "Version      : 3.9.2",
                "Release      : 50.2093",
                "Architecture : x86_64",
                "Size         : 84 M",
                "Source       : rockstor-3.9.2-50.2093.src.rpm",
                "Repository   : @System",
                "Packager     : None",
                "Buildtime    : Fri 29 Nov 2019 10:03:53 PM GMT",
                "Install time : Sun 01 Dec 2019 03:23:33 PM GMT",
                "Summary      : Btrfs Network Attached Storage (NAS) Appliance.",
                "URL          : http://rockstor.com/",
                "License      : GPL",
                "Description  : Software raid, snapshot capable NAS solution with built-in file",
                "             : integrity protection. Allows for file sharing between network",
                "             : attached devices.",
                "",
                "",
            ]
        )
        err.append([""])
        rc.append(0)
        expected_results.append(("3.9.2-50.2093", "2019-Nov-30"))
        # Source install where we key from the error message:
        dist_id.append("opensuse-tumbleweed")
        out.append(
            [
                "Loaded plugins: builddep, changelog, config-manager, copr, debug, debuginfo-install, download, generate_completion_cache, needs-restarting, playground, repoclosure, repodiff, repograph, repomanage, reposync",  # noqa E501
                "DNF version: 4.2.6",
                "cachedir: /var/cache/dnf",
                "No module defaults found",
                "",
            ]
        )
        err.append(["Error: No matching Packages to list", ""])
        rc.append(1)
        expected_results.append(("Unknown Version", None))

        for o, e, r, expected, distro in zip(out, err, rc, expected_results, dist_id):
            self.mock_run_command.return_value = (o, e, r)
            self.mock_distro.id.return_value = distro
            returned = rpm_build_info("rockstor")
            self.assertEqual(
                returned,
                expected,
                msg="Un-expected rpm_build_info() result:\n "
                "returned = ({}).\n "
                "expected = ({}).".format(returned, expected),
            )

    def test_pkg_latest_available(self):
        """
        This procedure was extracted from a fail through position at the end
        of rockstor_pkg_update_check() to enable discrete testing.
        Note that at time of extraction it was not believed to work as intended
        with dnf-yum.
        :return:
        """
        # CentOS Legacy yum - rockstor rpm installed with update available.
        # another process holding the rpm db (not relevant currently)
        arch = "x86_64"
        dist_id = ["rockstor"]
        out = [
            [
                "Loaded plugins: changelog, fastestmirror",
                "Loading mirror speeds from cached hostfile",
                " * base: mirrors.melbourne.co.uk",
                " * epel: mirrors.coreix.net",
                " * extras: mozart.ee.ic.ac.uk",
                " * updates: mirrors.coreix.net",
                "Resolving Dependencies",
                "--> Running transaction check",
                "---> Package rockstor.x86_64 0:3.9.2-50.2093 will be updated",
                "---> Package rockstor.x86_64 0:3.9.2-51.2089 will be an update",  # This is the parsed in legacy YUM
                "--> Finished Dependency Resolution",
                "",
                "Dependencies Resolved",
                "",
                "================================================================================",
                " Package          Arch           Version                Repository         Size",
                "================================================================================",
                "Updating:",
                " rockstor         x86_64         3.9.2-51.2089          localrepo          17 M",
                "",
                "Transaction Summary",
                "================================================================================",
                "Upgrade  1 Package",
                "",
                "Total download size: 17 M",
                "Exiting on user command",
                "Your transaction was saved, rerun it with:",
                " yum load-transaction /tmp/yum_save_tx.2019-12-02.10-37.0b42CF.yumtx",
                "",
            ]
        ]
        err = [
            [
                "Existing lock /var/run/yum.pid: another copy is running as pid 18540.",
                "Another app is currently holding the yum lock; waiting for it to exit...",
                "  The other application is: yum",
                "    Memory :  35 M RSS (712 MB VSZ)",
                "    Started: Mon Dec  2 10:37:13 2019 - 00:01 ago",
                "    State  : Sleeping, pid: 18540",
                "Another app is currently holding the yum lock; waiting for it to exit...",
                "  The other application is: yum",
                "    Memory :  35 M RSS (712 MB VSZ)",
                "    Started: Mon Dec  2 10:37:13 2019 - 00:03 ago",
                "    State  : Sleeping, pid: 18540",
                "",
            ]
        ]
        rc = [1]
        expected_result = ["3.9.2-51.2089"]
        # CentOS Legacy yum - rockstor rpm installed with update available.
        # no rpm db lock in place
        dist_id.append("rockstor")
        out.append(
            [
                "Loaded plugins: changelog, fastestmirror",
                "Loading mirror speeds from cached hostfile",
                " * base: mirrors.melbourne.co.uk",
                " * epel: mirrors.coreix.net",
                " * extras: mozart.ee.ic.ac.uk",
                " * updates: mozart.ee.ic.ac.uk",
                "Resolving Dependencies",
                "--> Running transaction check",
                "---> Package rockstor.x86_64 0:3.9.2-50.2093 will be updated",
                "---> Package rockstor.x86_64 0:3.9.2-51.2089 will be an update",
                "--> Finished Dependency Resolution",
                "",
                "Dependencies Resolved",
                "",
                "================================================================================",
                " Package          Arch           Version                Repository         Size",
                "================================================================================",
                "Updating:",
                " rockstor         x86_64         3.9.2-51.2089          localrepo          17 M",
                "",
                "Transaction Summary",
                "================================================================================",
                "Upgrade  1 Package",
                "",
                "Total download size: 17 M",
                "Exiting on user command",
                "Your transaction was saved, rerun it with:",
                " yum load-transaction /tmp/yum_save_tx.2019-12-02.10-47.uHJM6L.yumtx",
                "",
            ]
        )
        err.append([""])
        rc.append(1)
        expected_result.append("3.9.2-51.2089")
        # Tumblweed dnf-yum - no rockstor rpm installed but one available.
        dist_id.append("opensuse-tumbleweed")
        out.append(
            [
                "Local Repository                                2.9 MB/s | 3.0 kB     00:00    ",
                "No match for argument: rockstor",
                "",
            ]
        )
        err.append(
            [
                "Package rockstor available, but not installed.",
                "Error: No packages marked for upgrade.",
                "",
            ]
        )
        rc.append(1)
        expected_result.append(None)
        # Leap15.1 dnf-yum - rockstor package installed with update available:
        dist_id.append("opensuse-leap")
        out.append(
            [
                "Last metadata expiration check: 0:00:10 ago on Mon 02 Dec 2019 06:22:10 PM GMT.",
                "Dependencies resolved.",
                "================================================================================",
                " Package          Architecture   Version                Repository         Size",
                "================================================================================",
                "Upgrading:",
                " rockstor         x86_64         3.9.2-51.2089          localrepo          15 M",
                "",
                "Transaction Summary",
                "================================================================================",
                "Upgrade  1 Package",
                "",
                "Total size: 15 M",
                "",
            ]
        )
        err.append(["Operation aborted.", ""])
        rc.append(1)
        expected_result.append("3.9.2-51.2089")

        for o, e, r, expected, distro in zip(out, err, rc, expected_result, dist_id):
            self.mock_run_command.return_value = (o, e, r)
            returned = pkg_latest_available("rockstor", arch, distro)
            self.assertEqual(
                returned,
                expected,
                msg="Un-expected pkg_latest_available('rockstor') result:\n "
                "returned = ({}).\n "
                "expected = ({}).".format(returned, expected),
            )
