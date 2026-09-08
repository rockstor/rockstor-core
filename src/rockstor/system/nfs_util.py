"""
Copyright (joint work) 2026 The Rockstor Project <https://rockstor.com>

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

import os
import shutil
import time
from tempfile import mkstemp

from system.constants import MKDIR, MOUNT, UMOUNT, RMDIR, NFS_CONFIG, NFS_EXPORT_ROOT
from system.osi import run_command, is_mounted, toggle_path_rw

EXPORTFS = "/usr/sbin/exportfs"


"""
This file is to contain intentionally low-level facilities.
Some may be directly involved in Django model definitions.
It is therefor imperative/required that no related Django
model be import as this creates a circular dependency:
I.e.:
- Model requires this file's contents to initialise.
- This file requires related model to be initialised.
"""


def nfs4_mount_teardown(export_paths: list[str]):
    """
    If the passed path is mounted:
    1. Do a lazy unmount and check every second for 10 seconds before force unmounting.
    2. Ensure mount point dir is read-write.
    3. Remove mount point dir.
    :param export_paths: Bind mount points for NFS exports e.g.: `/export/nfs_export1`
    N.B. Moved from system.osi.
    """
    # N.B. candidate for parallelisation.
    for export_path in export_paths:
        if not export_path.startswith(NFS_EXPORT_ROOT):
            continue
        if is_mounted(export_path):
            # -l Lazy: detach fs now, clean-up referendes to the fs once no longer busy.
            run_command([UMOUNT, "-l", export_path], log=True)
            # Re-test mount status for 10 seconds, once unmounted make mount point dir rw.
            unmounted: bool = False
            for i in range(10):
                if not is_mounted(export_path):
                    unmounted = True
                    break
                    # return run_command([RMDIR, export_path])
                time.sleep(1)
            if not unmounted:  # still, then force unmount.
                run_command([UMOUNT, "--force", export_path], log=True)
            # Ensure mount point is not read-only so we can clean up.
            toggle_path_rw(export_path, rw=True)
        # Check mount point exists before attempting to remove it.
        if os.path.exists(export_path):
            run_command([RMDIR, export_path])
    return True


def bind_mount(mnt_pt, export_pt):
    """
    Convenience wrapper around:
    - `mkdir /export/share-name` if a mount does not already exist there.
    - `mount --bind mnt_pt export_pt`
    N.B. Moved from system.osi.
    :param mnt_pt: Share mount path, e.g.: `/mnt2/nfs_export1`
    :param export_pt: Where to bind mount for NFS exporting: e.g.: `/export/nfs_export1`
    :return: o, e, rc from mount command, or True if already mounted.
    """
    if not is_mounted(export_pt):
        run_command([MKDIR, "-p", export_pt])
        toggle_path_rw(export_pt, rw=False)
        return run_command([MOUNT, "--bind", mnt_pt, export_pt])
    return True


def valid_export(options: str, mapping: str) -> bool:
    """
    Runs `exportfs -i -o options mapping` to validate the passed parameters.
    -i ignores /etc/exports and files under /etc/exports.d & enforces default
      options where not specified.
    On unfavourable outcome (rc != 0 currently) we return False.
    :param options: NFS exportfs options (-o) e.g. "ro,sync,insecure"
    :param mapping: NFS exportfs mapping e.g. "192.168.2.2:/export/nfs_export2"
    :return: True if test export executed without issue. False otherwise
    """
    out, err, rc = run_command(
        [EXPORTFS, "-i", "-o", options, mapping], throw=False, log=True
    )
    if rc != 0:
        return False
    return True


def reexport_all() -> bool:
    """
    Runs `exportfs -ra` to re-assert all exports in /etc/exports & in files under
    /etc/exports.d by syncing their content to /var/lib/nfs/etab.
    N.B. Also unexports any prior exports no longer found in the above files.
    From 'man exportfs':
    "-a     Export or unexport all directories."
    # -r Reexport all and sync /var/lib/nfs/etab with /etc/exports and
    files under /etc/exports.d.
    :return:
    """
    out, err, rc = run_command([EXPORTFS, "-ra"], throw=False, log=True)
    if rc != 0:
        return False
    return True


def refresh_nfs_exports(exports: dict):
    """
    The master NFS export table is /var/lib/nfs/etab, informed by /etc/exports and the
    files under /etc/exports.d. We manage only the contents of /etc/exports:
    - refreshes are whole-sale all-share looped calls to `exportfs -i -o ...`
      to validate the options and mappings before creating that Shares nfs export line.
    - a subsequent call to `exportfs -ra` to assert the new contents of /etc/exports.
    N.B. `exportfs -ra` validates hostname, ommiting their config if resolution fails.
    #
    See: remove_nfs_export() for per share remove edits after Pool management delete.
    Example exports dict
    {'export_point': [{'client_str': 'www.example.com',
                       'option_list': 'rw,insecure,'
                       'mnt_pt': mnt_pt,},],
                       ...}
    if 'clients' is an empty list, then unmount and cleanup.
    N.B. Moved from system.osi.
    """
    fo, npath = mkstemp()
    with open(npath, "w") as efo:
        # Associated export paths export_path.g. `/export/nfs_export1`.
        export_paths: list = []
        for export_path in exports.keys():
            if len(exports[export_path]) == 0:
                #  do share tear down at the end, only snaps here
                if len(export_path.split("/")) == 4:
                    nfs4_mount_teardown([export_path])
                else:
                    export_paths.append(export_path)
                continue
            if not is_mounted(export_path):
                bind_mount(exports[export_path][0]["mnt_pt"], export_path)
            client_str = ""
            admin_host = None
            for c in exports[export_path]:
                if not valid_export(
                    options=c["option_list"], mapping=f"{c['client_str']}:{export_path}"
                ):
                    continue  # skip invalid options or client:export values.
                client_str = (
                    f"{client_str} {c['client_str']}({c['option_list']})".strip()
                )
                if "admin_host" in c:
                    admin_host = c["admin_host"]
            if admin_host is not None:
                if not valid_export(
                    options="rw,no_root_squash", mapping=f"{admin_host}:{export_path}"
                ):
                    continue  # skip invalid admin_host config.
                client_str = f"{client_str} {admin_host}(rw,no_root_squash)"
            export_str = f"{export_path} {client_str}\n"
            efo.write(export_str)
        nfs4_mount_teardown(export_paths)
    shutil.move(npath, NFS_CONFIG)
    return reexport_all()


def remove_nfs_export(share_name_list: list[str]) -> bool:
    """
    Intended as a light-weight option to remove all NFS export entries
    pertaining to the passed list of Share.names. Intentionally low-level
    to facilitate rapid adaptation of /etc/exports to mass Share removal
    such as when a Pool's management is deleted.
    Requires follow-up call to reexport_all().
    :param share_name_list: List of Share names to remove, if found, in /etc/exports.
    :return: Bool on changes written.
    """
    if not os.path.exists(NFS_CONFIG) or share_name_list == []:
        return False
    nfs_modified: bool = False
    fh, npath = mkstemp()
    with open(NFS_CONFIG, "r") as nfs_exports, open(npath, "w") as temp_file:
        for line in nfs_exports:
            if any(
                line.startswith(f"{NFS_EXPORT_ROOT}{share_name}")
                for share_name in share_name_list
            ):
                nfs_modified = True
                continue
            else:
                temp_file.write(line)
    if nfs_modified:
        shutil.move(npath, NFS_CONFIG)
        return nfs_modified
    else:
        os.remove(npath)
    return False
