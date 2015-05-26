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

from rest_framework import status
from rest_framework.test import APITestCase
import mock
from mock import patch

# functionality for all API tests.

class RockstorAPITests(object):
    # fixtures = ['fix1.json']
    # BASE_URL = '/api/shares'

    @classmethod
    def setUpClass(self):

        # error handling run_command mocks
        self.patch_run_command = patch('storageadmin.util.run_command')
        self.mock_run_command = self.patch_run_command.start()
        self.mock_run_command.return_value = True

    @classmethod
    def tearDownClass(self):
        patch.stopall()
