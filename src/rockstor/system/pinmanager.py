"""
Copyright (c) 2012-2016 RockStor, Inc. <http://rockstor.com>
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

from storageadmin.models import (Pincard, EmailClient)

def email_notification_enabled():
    #Check for email notifications state
    #required for password reset over root user (Pincard + otp via mail)
    try:
        mail_accounts = EmailClient.objects.filter().count()
    except EmailClient.DoesNotExist:
        mail_accounts = 0
        
    has_mail = True if mail_accounts > 0 else False

    return has_mail

def has_pincard(user):
    #Check if user has already a Pincard
    try:
        pins = Pincard.objects.filter(user=int(user.uid)).count()
    except Pincard.DoesNotExist:
        pins = 0
    
    has_pincard = True if (pins == 24) else False

    return has_pincard

def pincard_states(user):
    #If user has a Pincard that means already allowed to have one, so avoid computing
    #If selected user is a managed one allowed to have a pincard_allowed
    #If user is uid 0 (root) and mail notifications enabled -> ok Pincard
    #Otherwise 'otp' third state : allowed to have a Pincard, but mail notifications required
    pincard_allowed = 'no'
    pincard_present = has_pincard(user)
    if not pincard_present:
        if user.managed_user:
            pincard_allowed = 'yes'
        else:
            if int(user.uid) == 0:
                pincard_allowed = 'yes' if email_notification_enabled() else 'otp'
            else:
                pincard_allowed = 'no'
            
    else:
        pincard_allowed = 'yes'
        
    return pincard_allowed, pincard_present