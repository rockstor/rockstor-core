import logging
import os
from django.db import transaction
from rest_framework.response import Response
from smart_manager.models import Service
from smart_manager.views import BaseServiceDetailView
from storageadmin.util import handle_exception
from system.nut import configure_nut
from system.services import systemctl

logger = logging.getLogger(__name__)


class NUTServiceView(BaseServiceDetailView):
    service_name = 'nut'

    @transaction.atomic
    def post(self, request, command):
        """
        execute a command on the service
        """
        with self._handle_exception(request):
            service = Service.objects.get(name=self.service_name)
            if command == 'config':
                try:
                    # todo sort our default here prior to save.
                    config = request.data.get('config')
                    configure_nut(config)
                    self._save_config(service, config)
                except Exception, e:
                    logger.exception(e)
                    e_msg = ('NUT could not be configured. Please try again')
                    handle_exception(Exception(e_msg), request)
            else:
                # maybe a try exception around the switch.
                # we are assuming if command is not config its start or other
                self._switch_nut(command)
        return Response()

    @staticmethod
    def _switch_nut(switch):
        if (switch == 'start'):
            # should maybe use init_service_op here but both throw=true
            systemctl('nut-server', 'enable')
            systemctl('nut-server', 'start')
            systemctl('nut-monitor', 'enable')
            systemctl('nut-monitor', 'start')
        else:
            systemctl('nut-monitor', 'disable')
            systemctl('nut-monitor', 'stop')
            systemctl('nut-server', 'disable')
            systemctl('nut-server', 'stop')
