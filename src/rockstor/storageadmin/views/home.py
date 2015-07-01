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

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth import (authenticate, login, logout)

from storageadmin.models import (Appliance, Setup)
from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings
from rest_framework.renderers import JSONRenderer


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


def home(request):
    current_appliance = None
    try:
        current_appliance = Appliance.objects.get(current_appliance=True)
    except Exception:
        pass

    setup = Setup.objects.all()[0]
    context = {
        'request': request,
        'current_appliance': current_appliance,
        'setup_user': setup.setup_user,
        'page_size': settings.REST_FRAMEWORK['PAGE_SIZE'],
        'replica_data_port': settings.REPLICA_DATA_PORT,
        'replica_meta_port': settings.REPLICA_META_PORT,
    }
    if request.user.is_authenticated():
        return render_to_response('index.html',
                                  context,
                                  context_instance=RequestContext(request))
    else:
        if setup.setup_user:
            return render_to_response('login.html',
                                      context,
                                      context_instance=RequestContext(request))
        else:
            return render_to_response('setup.html',
                                      context,
                                      context_instance=RequestContext(request))


def logout_user(request):
    logout(request)
    return redirect('/')
