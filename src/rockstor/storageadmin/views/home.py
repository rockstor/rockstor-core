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

"""
Home view. login etc.. only for UI.
"""

from django.http import HttpResponse
from django.template import (Context, RequestContext)
from django.shortcuts import render_to_response
from django.template.loader import get_template
from django.contrib.auth import (authenticate, login, logout)

from storageadmin.models import Appliance, Setup
from storageadmin.serializers import SetupSerializer
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings
from rest_framework.renderers import JSONRenderer

import logging
logger = logging.getLogger(__name__)

def login_page(request):
    return render_to_response('login.html',
                              context_instance=RequestContext(request))
def login_submit(request):
    username = request.POST['login']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if (user is not None):
        if (user.is_active):
            login(request, user)
            return redirect('/home')
    messages.add_message(request, messages.INFO, 'Login incorrect!')
    return render_to_response('login.html',
                              context_instance=RequestContext(request))
    #return redirect('/login_page')

#@login_required(login_url='/login_page')
def home(request):
    current_appliance = None
    try:
        current_appliance = Appliance.objects.get(current_appliance=True)
    except Exception, e:
        pass 
    #setup = JSONRenderer().render(SetupSerializer(Setup.objects.all()[0]).data)
    setup = Setup.objects.all()[0]

    context = { 
        'request': request, 
        'current_appliance': current_appliance,
        'nginx_websocket_port': settings.NGINX_WEBSOCKET_PORT,
        'setup_user': setup.setup_user,
        'page_size': settings.PAGINATION['page_size']
    }
    logger.debug(request.user.is_authenticated())
    if request.user.is_authenticated():
        logger.debug("User is authenticated - rendering index")
        return render_to_response('index.html',
                context,
                context_instance=RequestContext(request))
    else:
        if setup.setup_user:
            logger.debug("User is setup but not authenticated \
                    - rendering login.html")
            return render_to_response('login.html',
                    context,
                    context_instance=RequestContext(request))
        else:
            logger.debug("User is not setup - rendering index.html")
            return render_to_response('setup.html',
                    context,
                    context_instance=RequestContext(request))


def logout_user(request):
    logout(request)
    return redirect('/')


