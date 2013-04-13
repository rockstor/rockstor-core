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

from django import forms

class DiskForm(forms.Form):
    name = forms.CharField(max_length=20)
    size = forms.IntegerField()
    parted = forms.BooleanField(required=False)

class PoolForm(forms.Form):
    name = forms.CharField(max_length=20)
    raid_level = forms.CharField(max_length=10, required=False)
    disks = forms.CharField(max_length=200)

class ShareForm(forms.Form):
    pool = forms.CharField(max_length=20)
    name = forms.CharField(max_length=100)
    size = forms.IntegerField()
    mount = forms.CharField(max_length=100, required=False)
    host_str = forms.CharField(max_length=256, required=False)
    mod_choice = forms.CharField(max_length=2, required=False)
    sync_choice = forms.CharField(max_length=5, required=False)
    security = forms.CharField(max_length=8, required=False)
