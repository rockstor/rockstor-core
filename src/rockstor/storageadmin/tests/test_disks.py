__author__ = 'samrichards'

from rest_framework import status
from rest_framework.test import APITestCase
import mock
from storageadmin.models import Disk


class DiskTests(APITestCase):
    fixtures = ['fix1.json']
    BASE_URL = '/api/disks'

    def test_disk_scan(self):
        self.client.login(username='admin', password='admin')
        response = self.client.post(('%s/scan' % self.BASE_URL), data=None,
        format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @mock.patch('storageadmin.views.disk.wipe_disk')
    def test_disk_wipe(self, mock_wipe_disk):
        url = ('%s/sdb/wipe' % self.BASE_URL)
        self.client.login(username='admin', password='admin')
        mock_wipe_disk.return_value = True
        response = self.client.post(url, data=None, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_wipe_disk.side_effect = Exception()
        response = self.client.post(url, data=None, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['detail'], 'Failed to wipe the disk due to a system error.')
