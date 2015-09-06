import logging
import os
from django.db import transaction
from rest_framework.response import Response
from smart_manager.models import Service
from smart_manager.views import BaseServiceDetailView
from storageadmin.util import handle_exception
from system.nut import configure_nut
from system.pkg_mgmt import install_pkg
from system.services import systemctl

logger = logging.getLogger(__name__)


class NUTServiceView(BaseServiceDetailView):
    service_name = 'nut'

    @transaction.commit_on_success
    def post(self, request, command):
        """
        execute a command on the service
        """
        e_msg = ('Failed to %s NUT service due to system error.' %
                 command)
        with self._handle_exception(request, e_msg):
            if (
            not os.path.exists('/usr/lib/systemd/system/nut-server.service')):
                install_pkg('nut')
                install_pkg('nut-xml')
            if command == 'config':
                service = Service.objects.get(name=self.service_name)
                # defaults can be provided in second parameter {dictionary: x}
                config = request.data.get('config', {'upsname': 'rockups', })
                # initial check on config type just in case
                if type(config) != dict:
                    e_msg = ('config dictionary is required input')
                    handle_exception(Exception(e_msg), request)
                # first pass sanity check on minimum requirements
                for option in ('upsname', 'upsuser', 'upspassword',):
                    if option not in config:
                        e_msg = ('%s is missing in config' % option)
                        handle_exception(Exception(e_msg), request)
                    if config[option] is None or config[option] == '':
                        e_msg = ('%s cannot be empty' % option)
                        handle_exception(Exception(e_msg), request)

                # if ('aux' not in config):
                #     e_msg = ('aux is missing in config: %s' % config)
                #     handle_exception(Exception(e_msg), request)
                # if (type(config['aux']) != list):
                #     e_msg = ('aux must be a list in config: %s' % config)
                #     handle_exception(Exception(e_msg), request)

                # now we have min config save it
                self._save_config(service, config)

                # pass config whole sale onto specialized function
                configure_nut(config)
            else:
                # we are assuming if command is not config its start or other
                self._switch_nut(command)
        return Response()

    @staticmethod
    def _switch_nut(switch):
        if (switch == 'start'):
            # should maybe use init_service_op here but both throw=true
            systemctl('nut-server', 'enable')
            systemctl('nut-server', 'start')

        else:
            systemctl('nut-server', 'disable')
            systemctl('nut-server', 'stop')
