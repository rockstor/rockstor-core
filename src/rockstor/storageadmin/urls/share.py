"""
Copyright (c) 2012-2013 RockStor, Inc. <http://rockstor.com>
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

from django.conf.urls.defaults import patterns, url
from storageadmin.views import (ShareView, ShareNFSView, ShareSambaView,
                                ShareACLView, SnapshotView, ShareIscsiView)

urlpatterns = patterns(
    '',
    url(r'^$', ShareView.as_view(), name='share-view'),
    url(r'^(?P<sname>[A-Za-z]+[A-Za-z0-9_]*)/$', ShareView.as_view(),
        name='share-view'),

    url(r'^(?P<sname>[A-Za-z]+[A-Za-z0-9_]*)/nfs/$', ShareNFSView.as_view(),
        name='nfs-view'),
    url(r'^(?P<sname>[A-Za-z]+[A-Za-z0-9_]*)/nfs/(?P<export_id>[0-9]+)/$',
        ShareNFSView.as_view(), name='nfs-view'),

    url(r'^(?P<sname>[A-Za-z]+[A-Za-z0-9_]*)/samba/$',
        ShareSambaView.as_view(), name='samba-view'),

    url(r'^(?P<sname>[A-Za-z]+[A-Za-z0-9_]*)/snapshots/$',
        SnapshotView.as_view(), name='snapshot-view'),
    url(r'^(?P<sname>[A-Za-z]+[A-Za-z0-9_]*)/snapshots/(?P<snap_name>.*)/$',
        SnapshotView.as_view(), name='snapshot-view'),

    url(r'^(?P<sname>[A-Za-z]+[A-Za-z0-9_]*)/iscsi/$', ShareIscsiView.as_view(),
        name='share-iscsi-view'),

    url(r'^(?P<sname>[A-Za-z]+[A-Za-z0-9_]*)/acl/$', ShareACLView.as_view(),
        name='acl-view'),
)
