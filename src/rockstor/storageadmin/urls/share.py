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
                                ShareACLView, SnapshotView, ShareIscsiView,
                                ShareCommandView)

share_regex = r'[A-Za-z]+[A-Za-z0-9_]*'
snap_regex = share_regex
snap_command = 'rollback|clone'

urlpatterns = patterns(
    '',
    url(r'^$', ShareView.as_view(), name='share-view'),
    url(r'^/(?P<sname>%s)$' % share_regex, ShareView.as_view(),
        name='share-view'),

    url(r'^/(?P<sname>%s)/nfs$' % share_regex, ShareNFSView.as_view(),
        name='nfs-view'),
    url(r'^/(?P<sname>%s)/nfs/(?P<export_id>[0-9]+)$' % share_regex,
        ShareNFSView.as_view(), name='nfs-view'),

    url(r'^/(?P<sname>%s)/samba$' % share_regex, ShareSambaView.as_view(),
        name='samba-view'),

    url(r'^/(?P<sname>%s)/snapshots$' % share_regex,
        SnapshotView.as_view(), name='snapshot-view'),
    url(r'^/(?P<sname>%s)/snapshots/(?P<snap_name>%s)$' % (share_regex,
                                                          snap_regex),
        SnapshotView.as_view(), name='snapshot-view'),
    url(r'^/(?P<sname>%s)/snapshots/(?P<snap_name>%s)/(?P<command>%s)$' %
        (share_regex, snap_regex, snap_command), SnapshotView.as_view()),

    url(r'^/(?P<sname>[A-Za-z]+[A-Za-z0-9_]*)/iscsi/$',
        ShareIscsiView.as_view(), name='share-iscsi-view'),

    url(r'^/(?P<sname>%s)/acl$' % share_regex, ShareACLView.as_view(),
        name='acl-view'),

    url(r'^/(?P<sname>%s)/(?P<command>clone)$' % share_regex,
        ShareCommandView.as_view()),
)
