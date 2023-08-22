"""
Copyright (c) 2012-2023 RockStor, Inc. <https://rockstor.com>
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
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout

from storageadmin.models import Appliance, Setup, UpdateSubscription
from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings

import logging

logger = logging.getLogger(__name__)


def login_page(request):
    return render(request, "login.html")


def login_submit(request):
    username = request.POST["login"]
    password = request.POST["password"]
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            login(request, user)
            return redirect("/home")
    messages.add_message(request, messages.INFO, "Login incorrect!")
    return render(request, "login.html")


def home(request):
    current_appliance = None
    try:
        current_appliance = Appliance.objects.get(current_appliance=True)
    except Exception:
        pass

    setup = Setup.objects.all()[0]
    update_channel = "Testing"
    stable_name = "Stable"
    if UpdateSubscription.objects.filter(name=stable_name, status="active").exists():
        update_channel = stable_name

    context = {
        "request": request,
        "current_appliance": current_appliance,
        "setup_user": setup.setup_user,
        "page_size": settings.REST_FRAMEWORK["PAGE_SIZE"],
        "update_channel": update_channel,
    }
    logger.debug("context={}".format(context))
    if request.user.is_authenticated:
        logger.debug("ABOUT TO RENDER INDEX")
        return render(request, "index.html", context)
    else:
        if setup.setup_user:
            logger.debug("ABOUT TO RENDER LOGIN")
            return render(request, "login.html", context)
        else:
            logger.debug("ABOUT TO RENDER SETUP")
            return render(request, "setup.html", context)


def logout_user(request):
    logout(request)
    return redirect("/")
