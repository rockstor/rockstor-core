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

import gzip
import json
import logging
import os
import string
import random  # Post Python3 move, replace random with: openid.cryptutil randomString
from time import sleep

from django.conf import settings
from django.db import transaction
from django_ztask.decorators import task
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.response import Response

import rest_framework_custom as rfc
from cli.rest_util import api_call
from smart_manager.models.service import Service, ServiceStatus
from storageadmin.models import ConfigBackup, RockOn
from storageadmin.serializers import ConfigBackupSerializer
from storageadmin.util import handle_exception
from system.config_backup import backup_config
from system.osi import md5sum, run_command

logger = logging.getLogger(__name__)
BASE_URL = "https://localhost/api"


def generic_post(url, payload):
    headers = {"content-type": "application/json"}
    try:
        api_call(url, data=payload, calltype="post", headers=headers, save_error=False)
        # Remove "password" indexed items from our dict payload to avoid logging them.
        if isinstance(payload, dict):
            payload.pop("password", None)
        else:
            logger.info("Non Dictionary payload")
        logger.info(
            "Successfully created resource: {}. Payload: {}".format(url, payload)
        )
    except Exception as e:
        logger.error(
            "Exception occurred while creating resource: {}. "
            "Payload: {}. Exception: {}. "
            "Moving on.".format(url, payload, e.__str__())
        )


def random_pass(length):
    """
    Generate a random password for use during user restore.
    Please see notes in import section on planned 'random' function improvements.
    :return: Random string request characters long.
    """
    all_chars = string.ascii_letters + string.digits + string.punctuation
    return "".join((random.choice(all_chars)) for _ in range(length))


def restore_users_groups(ml):
    logger.info("Started restoring users and groups.")
    users = []
    groups = []
    # Dictionary to map group pk to group name. Used to re-establishes user
    # to group name relationship.
    groupname_from_pk = {}
    for m in ml:
        if m["model"] == "storageadmin.user":
            users.append(m["fields"])
        if m["model"] == "storageadmin.group":
            groupname_from_pk[m["pk"]] = m["fields"]["groupname"]
            groups.append(m["fields"])

    # order is important, first create all the groups and then users.
    for g in groups:
        generic_post("{}/groups".format(BASE_URL), g)
    for u in users:
        # Replace user record 'group' field pk value with resolved group name.
        u["group"] = groupname_from_pk[u["group"]]
        # users are created with a random password
        u["password"] = random_pass(128)
        generic_post("{}/users".format(BASE_URL), u)
    logger.info("Finished restoring users and groups.")


def restore_samba_exports(ml):
    logger.info("Started restoring Samba exports.")
    exports = []
    for m in ml:
        if m["model"] == "storageadmin.sambashare":
            exports.append(m["fields"])
    for e in exports:
        e["shares"] = []
        e["shares"].append(e["share"])
    generic_post("{}/samba".format(BASE_URL), exports)


def restore_nfs_exports(ml):
    logger.info("Started restoring NFS exports.")
    exports = []
    export_groups = {}
    adv_exports = {"entries": []}
    for m in ml:
        if m["model"] == "storageadmin.nfsexport":
            exports.append(m["fields"])
        elif m["model"] == "storageadmin.nfsexportgroup":
            m["fields"]["pk"] = m["pk"]
            export_groups[m["pk"]] = m["fields"]
        elif m["model"] == "storageadmin.advancednfsexport":
            adv_exports["entries"].append(m["fields"]["export_str"])
    for e in exports:
        if len(e["mount"].split("/")) != 3:
            logger.info("skipping nfs export with mount: {}".format(e["mount"]))
            continue
        e["shares"] = [e["mount"].split("/")[2]]
        payload = dict(export_groups[e["export_group"]], **e)
        generic_post("{}/nfs-exports".format(BASE_URL), payload)
    generic_post("{}/adv-nfs-exports".format(BASE_URL), adv_exports)
    logger.info("Finished restoring NFS exports.")


def restore_services(ml):
    logger.info("Started restoring services.")
    services = {}
    for m in ml:
        if m["model"] == "smart_manager.service":
            name = m["fields"]["name"]
            config = m["fields"]["config"]
            pkid = m["pk"]
            if config is not None:
                config = json.loads(config)
                services[name] = {"conf": {"config": config}, "id": pkid}
    for s in services:
        generic_post(
            "{}/sm/services/{}/config".format(BASE_URL, s), services[s]["conf"]
        )
        # Turn the service ON if it is ON in backup AND currently OFF
        so = Service.objects.get(name=s)
        if (
            validate_service_status(ml, services[s]["id"])
            and not ServiceStatus.objects.get(service_id=so.id).status
        ):
            generic_post("{}/sm/services/{}/start".format(BASE_URL, s), {})
    logger.info("Finished restoring services.")


def validate_service_status(ml, pkid):
    """
    Parses a model list (ml) and returns True if the service identified by
    its id (pkid) was ON in the config backup.
    :param ml: dict of models list
    :param pkid: int
    :return: True
    """
    for m in ml:
        if (
            m["model"] == "smart_manager.servicestatus"
            and m["fields"]["service"] is pkid
        ):
            return m["fields"]["status"]


def restore_scheduled_tasks(ml):
    """
    Parses the config backup to re-create a valid POST request to be sent to the
    sm/tasks API in order to re-create the scheduled task(s) in question.
    If multiple tasks are to be re-created, the config for each one is stored
    inside a list that is then looped through to send an api request for each task.
    Need the following info for each request:
        - name
        - task_type
        - crontab
        - crontabwindow
        - meta
        - enabled
    :param ml: list of smart_manager models of interest as parsed by restore_config()
    """
    logger.info("Started restoring scheduled tasks.")
    tasks = []
    for m in ml:
        if m["model"] == "smart_manager.taskdefinition":
            name = m["fields"]["name"]
            task_type = m["fields"]["task_type"]
            crontab = m["fields"]["crontab"]
            crontabwindow = m["fields"]["crontabwindow"]
            enabled = m["fields"]["enabled"]
            json_meta = m["fields"]["json_meta"]
            if json_meta is not None:
                jmeta = json.loads(json_meta)
            taskdef = {
                "name": name,
                "task_type": task_type,
                "crontab": crontab,
                "crontabwindow": crontabwindow,
                "enabled": enabled,
                "meta": jmeta,
            }
            tasks.append(taskdef)
    for t in tasks:
        generic_post("{}/sm/tasks/".format(BASE_URL), t)
    logger.info("Finished restoring scheduled tasks.")


def restore_rockons(ml):
    """
    Parses and filter the model list input (ml) to gather all the information
    required to install a rock-on. The result is then sent to the rockon API.
    Notably, we need to filter the input and keep only the information from rock-ons
    that were installed at the time of the backup. We will thus get the following:
    - rock-on name and its primary key
    - custom_config: need everything
    - container(s): need only its id.
    - volume(s): need everything
    - ports: need everything
    - device(s): need everything
    - environment variable(s): need everything
    - label(s) (may need refactoring of rockon_id update() process so that it can
        be triggered from here as well): need everything

    For a given rock-on, the final request should follow the syntax below:
    {
    'environment': {'GID': '1000', 'UID': '1000', 'GIDLIST': '1000'},
    'devices': {'VAAPI': ''},
    'ports': {'8096': 8096, '8920': 8920},
    'shares': {'emby-media': '/media', 'emby-conf': '/config'}
    }

    :param ml: dict of models present in the config backup
    :return:
    """
    logger.info("Started restoring rock-ons.")
    rockons = validate_rockons(ml)
    logger.info("The following rock-ons will be restored: {}.".format(rockons))
    if len(rockons) > 0:
        for rid in rockons:
            # Get config for initial install
            validate_install_config(ml, rid, rockons)
            # Install
            rockon_transition_checker.async(rid, rockons)
            restore_install_rockon.async(rid, rockons, command="install")

            # Get config for post-install update
            validate_update_config(ml, rid, rockons)
            # Update
            if bool(rockons[rid]["shares"]) or bool(rockons[rid]["labels"]):
                # docker stop
                rockon_transition_checker.async(rid, rockons)
                restore_install_rockon.async(rid, rockons, command="stop")
                # Start update
                rockon_transition_checker.async(rid, rockons)
                restore_install_rockon.async(rid, rockons, command="update")
    logger.info("Finished restoring rock-ons.")


@task()
def rockon_transition_checker(rid, rockons):
    cur_wait = 0
    while RockOn.objects.filter(state__contains="pending").exists():
        sleep(2)
        cur_wait += 2
        if cur_wait > 30:
            logger.error(
                "Waited too long for the previous rock-on to install..."
                "Stop trying to install the rock-on ({})".format(rockons[rid]["rname"])
            )
        break


@task()
def restore_install_rockon(rid, rockons, command):
    logger.info(
        "Send {} command to the rock-ons api for the following rock-on: {}".format(
            command, rockons[rid]["rname"]
        )
    )
    generic_post(
        "{}/rockons/{}/{}".format(BASE_URL, rockons[rid]["new_rid"], command),
        rockons[rid],
    )


def validate_install_config(ml, rid, rockons):
    """
    Given a dict of list of models from a config backup, this function builds a dict of the
    parameters to install a rock-on identified by its ID. These parameters are the container(s),
    share(s), port(s), device(s), environment variable(s), and custom_configuration.
    :param ml: dict of models present in the config backup
    :param rid: rockon ID
    :param rockons: parent dict of rock-ons to be updated
    :return: the same dict updated with the installation parameters present in config backup
    """
    rockons[rid]["containers"] = []
    rockons[rid]["shares"] = {}
    rockons[rid]["ports"] = {}
    rockons[rid]["devices"] = {}
    rockons[rid]["environment"] = {}
    rockons[rid]["cc"] = {}
    # Get container(s) id(s)
    for m in ml:
        if m["model"] == "storageadmin.dcontainer" and m["fields"]["rockon"] is rid:
            rockons[rid]["containers"].append(m["pk"])
    # For each container_id:
    for cid in rockons[rid].get("containers"):
        # get shares
        update_rockon_shares(cid, ml, rid, rockons)

        # get ports
        for m in ml:
            if m["model"] == "storageadmin.dport" and m["fields"]["container"] is cid:
                hostp = m["fields"]["hostp"]
                containerp = m["fields"]["containerp"]
                rockons[rid]["ports"].update({hostp: containerp})

        # get devices
        for m in ml:
            if (
                m["model"] == "storageadmin.dcontainerdevice"
                and m["fields"]["container"] is cid
            ):
                dev = m["fields"]["dev"]
                val = m["fields"]["val"]
                rockons[rid]["devices"].update({dev: val})

        # get environment
        update_rockon_env(cid, ml, rid, rockons)
    # get cc
    for m in ml:
        if m["model"] == "storageadmin.dcustomconfig" and m["fields"]["rockon"] is rid:
            key = m["fields"]["key"]
            val = m["fields"]["val"]
            rockons[rid]["cc"].update({key: val})


def validate_update_config(ml, rid, rockons):
    """
    Get config for the rock-on update procedure.
    Final request data should be in the form:
    {u'labels': {u'testlabel01': u'alpinesingle', u'testlabel02': u'alpinesingle'}, u'shares': {}}
    :param ml: dict of models present in the config backup
    :param rid: ID of a rock-on
    :param rockons: dict of rock-ons parameters to be updated
    :return: the same dict of rock-ons parameters updated with post-install customization options
    """
    # Reset both 'shares' AND 'labels' to empty dicts
    rockons[rid]["shares"] = {}
    rockons[rid]["labels"] = {}
    # For each container_id:
    for cid in rockons[rid].get("containers"):
        # get shares
        update_rockon_shares(cid, ml, rid, rockons, uservol=True)

        # get labels
        for m in ml:
            if (
                m["model"] == "storageadmin.dcontainerlabel"
                and m["fields"]["container"] is cid
            ):
                label = m["fields"]["val"]
                cname = m["fields"]["key"]
                rockons[rid]["labels"].update({label: cname})


def update_rockon_env(cid, ml, rid, rockons):
    """
    Builds a dictionary with env_key:value for a given container id (cid)
    of a given rock-on (rid) as present in a config backup (ml).
    """
    # todo: When the env variable is PUID or PGID, try fetching value by name with
    #     current system in case an update is needed.
    for m in ml:
        if (
            m["model"] == "storageadmin.dcontainerenv"
            and m["fields"]["container"] is cid
        ):
            key = m["fields"]["key"]
            val = m["fields"]["val"]
            rockons[rid]["environment"].update({key: val})


def update_rockon_shares(cid, ml, rid, rockons, uservol=False):
    """
    Builds a dictionary with share_name:volume mapping for a given container id (cid)
    of a given rock-on (rid) as present in a config backup (ml).
    :param cid: ID of a container
    :param ml: dict of models present in the config backup
    :param rid: ID of a rock-on
    :param rockons: dict of rock-ons paramaters to be updated
    :param uservol: boolean
    :return: the same dict of rock-ons parameters updated with share:volume mappings
    """
    for m in ml:
        if (
            m["model"] == "storageadmin.dvolume"
            and m["fields"]["container"] is cid
            and m["fields"]["uservol"] is uservol
        ):
            share_id = m["fields"]["share"]
            sname = get_sname(ml, share_id)
            dest_dir = m["fields"]["dest_dir"]
            if not uservol:
                rockons[rid]["shares"].update({sname: dest_dir})
            else:
                rockons[rid]["shares"].update({dest_dir: sname})


def validate_rockons(ml):
    """
    Takes a list of models from a backup and returns a list of names of the rockons
    that were installed as identified by their status of 'installed'. Notably,
    a rockon name is returned only if a rock-on with the same name is not
    currently installed on the machine.
    :param ml: dict of models from the config backup
    :return: dict of rock-ons names to be restored
    """
    # Update all rock-ons-related db information
    generic_post("{}/rockons/update".format(BASE_URL), {})

    rockons = {}
    # Filter rock-on that were installed in the backup
    for m in ml:
        if m["model"] == "storageadmin.rockon" and m["fields"]["state"] == "installed":
            rname = m["fields"]["name"]
            if (
                not RockOn.objects.filter(name=rname, state="installed").exists()
                and RockOn.objects.filter(name=rname).exists()
            ):
                ro = RockOn.objects.get(name=rname)
                rockons[m["pk"]] = {}
                rockons[m["pk"]]["new_rid"] = ro.id
                rockons[m["pk"]]["rname"] = m["fields"]["name"]
    return rockons


def get_sname(ml, share_id):
    """
    Takes a share ID and a database backup list of models and returns the
    name of the share.
    :param ml: dict of models from the config backup
    :param share_id: number ID of the share whose name is sought
    :return: string of the share name
    """
    for m in ml:
        if m["model"] == "storageadmin.share" and m["pk"] is share_id:
            sname = m["fields"]["name"]
    return sname


@task()
def restore_config(cbid):
    cbo = ConfigBackup.objects.get(id=cbid)
    fp = os.path.join(settings.MEDIA_ROOT, "config-backups", cbo.filename)
    gfo = gzip.open(fp)
    lines = gfo.readlines()
    sa_ml = json.loads(lines[0])
    sm_ml = json.loads(lines[1])
    gfo.close()
    restore_users_groups(sa_ml)
    restore_samba_exports(sa_ml)
    restore_nfs_exports(sa_ml)
    restore_services(sm_ml)
    # restore_dashboard(ml)
    # restore_appliances(ml)
    # restore_network(sa_ml)
    restore_scheduled_tasks(sm_ml)
    restore_rockons(sa_ml)


class ConfigBackupMixin(object):
    serializer_class = ConfigBackupSerializer


class ConfigBackupListView(ConfigBackupMixin, rfc.GenericView):
    def get_queryset(self, *args, **kwargs):
        for cbo in ConfigBackup.objects.all():
            fp = os.path.join(ConfigBackup.cb_dir(), cbo.filename)

            if not os.path.isfile(fp):
                cbo.delete()

            try:
                with gzip.open(fp, "rb") as f:
                    f.read()
            except IOError as e:
                logger.exception(e)
                logger.info(
                    "The file {} is not gzipped, so compress it now.".format(
                        cbo.filename
                    )
                )

                try:
                    o, err, rc = run_command(["/usr/bin/gzip", fp], log=True)
                except Exception as e:
                    # gzip returns rc == 2 if the destination file already exists
                    # so let's return an explicit error message to the user for this case
                    if e.rc == 2:
                        e_msg = (
                            "A destination file for the config backup file with the same "
                            "name ({}) already exists. Please remove it and try again.".format(
                                fp
                            )
                        )
                        # Delete file from system
                        run_command(["/bin/rm", "-f", fp], log=True)
                    else:
                        e_msg = (
                            "The backup config file ({}) couldn't be gzipped.\n"
                            "Reload the page to refresh the list of backups".format(fp)
                        )
                    cbo.delete()
                    handle_exception(Exception(e_msg), self.request)

                gz_name = "{}.gz".format(cbo.filename)
                cbo.filename = gz_name
                fp = os.path.join(ConfigBackup.cb_dir(), cbo.filename)
                cbo.md5sum = md5sum(fp)
                cbo.size = os.stat(fp).st_size
                cbo.save()

            fp_md5sum = md5sum(fp)
            if fp_md5sum != cbo.md5sum:
                logger.error(
                    "md5sum mismatch for {}. cbo: {} file: {}. "
                    "Deleting dbo.".format(cbo.filename, cbo.md5sum, fp_md5sum)
                )
                cbo.delete()
        return ConfigBackup.objects.filter().order_by("-id")

    @transaction.atomic
    def post(self, request):
        logger.debug("backing up config...")
        with self._handle_exception(request):
            cbo = backup_config()
            return Response(ConfigBackupSerializer(cbo).data)


class ConfigBackupDetailView(ConfigBackupMixin, rfc.GenericView):
    @transaction.atomic
    def delete(self, request, backup_id):
        with self._handle_exception(request):
            cbo = self._validate_input(backup_id, request)
            fp = os.path.join(ConfigBackup.cb_dir(), cbo.filename)
            if os.path.isfile(fp):
                os.remove(fp)
            cbo.delete()
            return Response()

    @transaction.atomic
    def post(self, request, backup_id):
        with self._handle_exception(request):
            command = request.data.get("command", "restore")
            if command == "restore":
                cbo = self._validate_input(backup_id, request)
                # models that need to be restored.
                # 1. User, Group, Accesskeys?
                # 2. SambaShare
                # 3. NFSExport, NFSExportGroup
                # 4. Service configs
                # 5. Appliances?
                # 6. Scheduled Tasks
                # 7. SFTP
                logger.debug("restore starting...")
                restore_config.async(cbo.id)
                logger.debug("restore submitted...")
        return Response()

    @staticmethod
    def _validate_input(backup_id, request):
        try:
            return ConfigBackup.objects.get(id=backup_id)
        except ConfigBackup.DoesNotExist:
            e_msg = ("Config backup for the id ({}) does not exist.").format(backup_id)
            handle_exception(Exception(e_msg), request)


class ConfigBackupUpload(ConfigBackupMixin, rfc.GenericView):
    parser_classes = (FileUploadParser, MultiPartParser)

    def get_queryset(self, *args, **kwargs):
        for cbo in ConfigBackup.objects.all():
            fp = os.path.join(ConfigBackup.cb_dir(), cbo.filename)
            if not os.path.isfile(fp):
                cbo.delete()
            fp_md5sum = md5sum(fp)
            if fp_md5sum != cbo.md5sum:
                logger.error(
                    "md5sum mismatch for {}. cbo: {} file: {}. "
                    "Deleting dbo".format(cbo.filename, cbo.md5sum, fp_md5sum)
                )
                cbo.delete()
        return ConfigBackup.objects.filter().order_by("-id")

    def post(self, request, format=None):
        with self._handle_exception(request):
            filename = request.data["file-name"]
            file_obj = request.data["file"]
            if ConfigBackup.objects.filter(filename=filename).exists():
                msg = (
                    "Config backup ({}) already exists. Uploading a "
                    "duplicate is not allowed."
                ).format(filename)
                handle_exception(Exception(msg), request)
            cbo = ConfigBackup.objects.create(filename=filename, config_backup=file_obj)
            cb_dir = ConfigBackup.cb_dir()
            if not os.path.isdir(cb_dir):
                os.mkdir(cb_dir)
            fp = os.path.join(cb_dir, filename)

            cbo.md5sum = md5sum(fp)
            cbo.size = os.stat(fp).st_size
            cbo.save()
            return Response(ConfigBackupSerializer(cbo).data)
