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

import pwd
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.db import transaction
from django.conf import settings
from storageadmin.models import SambaShare, User, SambaCustomConfig
from storageadmin.serializers import SambaShareSerializer
from storageadmin.util import handle_exception
import rest_framework_custom as rfc
from share import ShareMixin
from system.samba import refresh_smb_config, status, restart_samba
from fs.btrfs import mount_share

import logging

logger = logging.getLogger(__name__)


class SambaMixin(object):
    serializer_class = SambaShareSerializer
    DEF_OPTS = {
        "comment": "samba export",
        "browsable": "yes",
        "guest_ok": "no",
        "read_only": "no",
        "custom_config": None,
        "shadow_copy": False,
        "snapshot_prefix": None,
    }
    BOOL_OPTS = ("yes", "no")

    @staticmethod
    def _restart_samba():
        out = status()
        if out[2] == 0:
            restart_samba(hard=True)

    @classmethod
    def _validate_input(cls, rdata, smbo=None):
        options = {}
        def_opts = cls.DEF_OPTS
        if smbo is not None:
            def_opts = cls.DEF_OPTS.copy()
            def_opts["comment"] = smbo.comment
            def_opts["browsable"] = smbo.browsable
            def_opts["guest_ok"] = smbo.guest_ok
            def_opts["read_only"] = smbo.read_only
            def_opts["shadow_copy"] = smbo.shadow_copy

        options["comment"] = rdata.get("comment", def_opts["comment"])
        options["browsable"] = rdata.get("browsable", def_opts["browsable"])

        options["custom_config"] = rdata.get("custom_config", [])
        if type(options["custom_config"]) != list:
            e_msg = "Custom config must be a list of strings."
            handle_exception(Exception(e_msg), rdata)
        if options["browsable"] not in cls.BOOL_OPTS:
            e_msg = "Invalid choice for browsable. Possible choices are yes or no."
            handle_exception(Exception(e_msg), rdata)
        options["guest_ok"] = rdata.get("guest_ok", def_opts["guest_ok"])
        if options["guest_ok"] not in cls.BOOL_OPTS:
            e_msg = "Invalid choice for guest_ok. Possible options are yes or no."
            handle_exception(Exception(e_msg), rdata)
        options["read_only"] = rdata.get("read_only", def_opts["read_only"])
        if options["read_only"] not in cls.BOOL_OPTS:
            e_msg = "Invalid choice for read_only. Possible options are yes or no."
            handle_exception(Exception(e_msg), rdata)
        options["shadow_copy"] = rdata.get("shadow_copy", def_opts["shadow_copy"])
        if options["shadow_copy"]:
            options["snapshot_prefix"] = rdata.get(
                "snapshot_prefix", def_opts["snapshot_prefix"]
            )
            if (
                options["snapshot_prefix"] is None
                or len(options["snapshot_prefix"].strip()) == 0
            ):
                e_msg = (
                    "Invalid choice for snapshot_prefix. It must be a "
                    "valid non-empty string."
                )
                handle_exception(Exception(e_msg), rdata)

        return options

    @staticmethod
    def _set_admin_users(admin_users, smb_share):
        for au in admin_users:
            try:
                auo = User.objects.get(username=au)
            except User.DoesNotExist:
                # check if the user is a system user, then create a temp user
                # object.
                try:
                    system_user = pwd.getpwnam(au)
                    auo = User(
                        username=au,
                        uid=system_user.pw_uid,
                        gid=system_user.pw_gid,
                        admin=False,
                    )
                    auo.save()
                except KeyError:
                    # raise the outer exception as it's more meaningful to the
                    # user.
                    raise Exception("Requested admin user(%s) does not exist." % au)
            finally:
                auo.smb_shares.add(smb_share)


class SambaListView(SambaMixin, ShareMixin, rfc.GenericView):
    queryset = SambaShare.objects.all()

    @transaction.atomic
    def post(self, request):
        if isinstance(request.data, list):
            for se in request.data:
                smb_share = self.create_samba_share(se)
        else:
            smb_share = self.create_samba_share(request.data)
        refresh_smb_config(list(SambaShare.objects.all()))
        self._restart_samba()
        return Response(SambaShareSerializer(smb_share).data)

    def create_samba_share(self, rdata):
        if "shares" not in rdata:
            e_msg = "Must provide share names."
            handle_exception(Exception(e_msg), rdata)
        shares = [self._validate_share(rdata, s) for s in rdata["shares"]]
        options = self._validate_input(rdata)
        custom_config = options["custom_config"]
        del options["custom_config"]
        with self._handle_exception(rdata):
            for share in shares:
                if SambaShare.objects.filter(share=share).exists():
                    e_msg = ("Share ({}) is already exported via Samba.").format(
                        share.name
                    )
                    logger.error(e_msg)
                    smb_share = SambaShare.objects.get(share=share)
                    # handle_exception(Exception(e_msg), rdata)
                    continue
                mnt_pt = "{}{}".format(settings.MNT_PT, share.name)
                options["share"] = share
                options["path"] = mnt_pt
                smb_share = SambaShare(**options)
                smb_share.save()
                for cc in custom_config:
                    cco = SambaCustomConfig(smb_share=smb_share, custom_config=cc)
                    cco.save()
                if not share.is_mounted:
                    mount_share(share, mnt_pt)

                admin_users = rdata.get("admin_users", [])
                if admin_users is None:
                    admin_users = []
                self._set_admin_users(admin_users, smb_share)
        return smb_share


class SambaDetailView(SambaMixin, rfc.GenericView):
    def get(self, *args, **kwargs):
        try:
            data = SambaShare.objects.get(id=self.kwargs["smb_id"])
            serialized_data = SambaShareSerializer(data)
            return Response(serialized_data.data)
        except SambaShare.DoesNotExist:
            raise NotFound(detail=None)

    @transaction.atomic
    def delete(self, request, smb_id):
        try:
            smbo = SambaShare.objects.get(id=smb_id)
            SambaCustomConfig.objects.filter(smb_share=smbo).delete()
            smbo.delete()
        except:
            e_msg = ("Samba export for the id ({}) does not exist.").format(smb_id)
            handle_exception(Exception(e_msg), request)

        with self._handle_exception(request):
            refresh_smb_config(list(SambaShare.objects.all()))
            self._restart_samba()
            return Response()

    @transaction.atomic
    def put(self, request, smb_id):
        with self._handle_exception(request):
            try:
                smbo = SambaShare.objects.get(id=smb_id)
            except:
                e_msg = ("Samba export for the id ({}) does not exist.").format(
                    smb_id
                )
                handle_exception(Exception(e_msg), request)

            options = self._validate_input(request.data, smbo=smbo)
            custom_config = options["custom_config"]
            del options["custom_config"]
            smbo.__dict__.update(**options)
            admin_users = request.data.get("admin_users", [])
            if admin_users is None:
                admin_users = []
            for uo in User.objects.filter(smb_shares=smbo):
                if uo.username not in admin_users:
                    uo.smb_shares.remove(smbo)
            self._set_admin_users(admin_users, smbo)
            smbo.save()
            for cco in SambaCustomConfig.objects.filter(smb_share=smbo):
                if cco.custom_config not in custom_config:
                    cco.delete()
                else:
                    custom_config.remove(cco.custom_config)
            for cc in custom_config:
                cco = SambaCustomConfig(smb_share=smbo, custom_config=cc)
                cco.save()
            for smb_o in SambaShare.objects.all():
                if not smb_o.share.is_mounted:
                    mnt_pt = "%s%s" % (settings.MNT_PT, smb_o.share.name)
                    try:
                        mount_share(smb_o.share, mnt_pt)
                    except Exception as e:
                        logger.exception(e)
                        if smb_o.id == smbo.id:
                            e_msg = (
                                "Failed to mount share ({}) due to a low "
                                "level error."
                            ).format(smb_o.share.name)
                            handle_exception(Exception(e_msg), request)

            refresh_smb_config(list(SambaShare.objects.all()))
            self._restart_samba()
            return Response(SambaShareSerializer(smbo).data)
