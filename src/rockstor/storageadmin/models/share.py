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

from django.db import models
from storageadmin.models import Pool, Snapshot
from smart_manager.models import ShareUsage


class Share(models.Model):
	"""pool that this share is part of"""
	pool = models.ForeignKey(Pool)
	"""quota group this share is part of"""
	qgroup = models.CharField(max_length=100)
	"""name of the share, kind of like id"""
	name = models.CharField(max_length=4096, unique=True)
	"""id of the share. numeric in case of btrfs"""
	uuid = models.CharField(max_length=100, null=True)
	"""total size in KB"""
	size = models.BigIntegerField(default=0)
	owner = models.CharField(max_length=4096, default='root')
	group = models.CharField(max_length=4096, default='root')
	perms = models.CharField(max_length=9, default='755')
	toc = models.DateTimeField(auto_now=True)
	subvol_name = models.CharField(max_length=4096)
	replica = models.BooleanField(default=False)
	compression_algo = models.CharField(max_length=1024, null=True)
        rusage = models.BigIntegerField(default=0)
        eusage = models.BigIntegerField(default=0)

	class Meta:
		app_label = 'storageadmin'
