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
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

from fs.btrfs import umount_root
from system.constants import CHOWN, CHMOD
from system.osi import run_command
from huey.contrib.djhuey import task
import psutil



@task()
def chown(mnt_pt: str, owner: str, group: str | None = None, recursive: bool = False):
    """
    Constructs and runs a chown command, under our scheduler via a decorator.
    :param mnt_pt: subvol mount point.
    :param owner: e.g. "user" expected.
    :param group: e.g. "groupname" optional.
    :param recursive: optional, defaults to False.
    :return: out, err, rc from run_command.
    """
    cmd: list[str] = [
        CHOWN,
    ]
    if recursive:
        cmd.append("-R")
    if group is not None:
        owner = f"{owner}:{group}"
    cmd.extend([owner, mnt_pt])
    return run_command(cmd)


@task()
def chmod(mnt_pt: str, perm_bits: str, recursive: bool = False):
    """
    Constructs and runs a chmod command, under our scheduler via a decorator.
    Intended to be invoked from the @HUEY.signal(SIGNAL_COMPLETE) of
    @task(name="acl.chown"). To ensure we only change permissions after first
    completing the owner:group changes.
    :param mnt_pt: subvol mount point.
    :param perm_bits: e.g. 755 for rwx r-x r-x.
    :param recursive: Recursively apply.
    :return: out, err, rc from run_command.
    """
    cmd: list[str] = [
        CHMOD,
    ]
    if recursive:
        cmd.append("-R")
    cmd.extend([perm_bits, mnt_pt])
    return run_command(cmd)


@task()
def acl_change_manager(
    mnt_pt: str,
    owner: str,
    group: str | None = None,
    og_recursive: bool = False,
    perms: str = 755,
    p_recursive: bool = False,
    was_unmounted: bool = False,
):
    """
    Wrapper for chown then chmod serialized in the background, each with optional recursion,
    and each under their own locked (single instance) task.
    See: @HUEY.signal(SIGNAL_COMPLETE) for our Share.taskid stamp clean-up via clear_task_id
    :param mnt_pt:
    :param owner:
    :param group:
    :param og_recursive: owner:group recursive for chown.
    :param perms:
    :param p_recursive: permissions recursive for chmod.
    :param was_unmounted: Share status prior to ACL request.
    :return: Task
    """
    # We serialize the following by enquiing the first task, and awaiting it completion.
    # The following returns imidiately with a task result handler.
    chown_task_handler = chown(
        mnt_pt, owner, group, og_recursive
    )  # Returns immediately.
    chown_task_handler(blocking=True)  # Wait for task completion.
    chmod_task_handler = chmod(mnt_pt, perms, p_recursive)
    chmod_task_handler(blocking=True)  # Wait for task completion.
    # If this subvol was previously unmounted, return it to that state.
    if was_unmounted:
        umount_root(mnt_pt)


def chown_or_chmod_active(mnt_pt: str) -> bool:
    """
    Examines system process via psutils.
    Returns boolean if chown or chmod processes are found on the given mnt_pt.
    :param mnt_pt: subvol mount point.
    :return:
    """
    # Example proc.info entries:
    # {'status': 'running', 'cmdline': ['/usr/bin/chown', '-R', 'test2:test2', '/mnt2/rockons-root3'], 'name': 'chown'}
    # {'status': 'running', 'cmdline': ['/usr/bin/chmod', '-R', '770', '/mnt2/rockons-root3'], 'name': 'chmod'}
    for proc in psutil.process_iter(["name", "cmdline", "status"]):
        if proc.info["name"] == "chown" or proc.info["name"] == "chmod":
            if proc.info["cmdline"] != [] and proc.info["cmdline"][-1] == mnt_pt:
                return True
    return False
