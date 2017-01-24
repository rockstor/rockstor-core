"""
Copyright (c) 2012 RockStor, Inc. <http://rockstor.com>
This file is part of RockStor.

RockStor is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 3 of the License,
or (at your option) any later version.

RockStor is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

"""


class TapConfig(object):

    def __init__(self, uuid, location, sdetail):
        self.uuid = uuid
        self.location = location
        self.sdetail = sdetail


TAP_MAP = {
    'nfs-1': {'location': 'nfsd/nfsd_distrib',
              'sdetail': 'All NFS calls',
              'cb': 'process_nfsd_calls', },

    'nfs-2': {'location': 'nfsd/nfsd_distrib_client',
              'sdetail': 'NFS call distribution over clients',
              'cb': 'process_nfsd_calls', },

    'nfs-3': {'location': 'nfsd/nfsd_distrib_share',
              'sdetail': 'NFS call distribution over shares',
              'cb': 'share_distribution', },

    'nfs-4': {'location': 'nfsd/nfsd_distrib_share_client',
              'sdetail': 'NFS call distribution over clients and shares',
              'cb': 'share_client_distribution', },

    'nfs-5': {'location': 'nfsd/nfsd_distrib_uid_gid',
              'sdetail': 'NFS call distribution over uids and gids',
              'cb': 'nfs_uid_gid_distribution', },

    }
