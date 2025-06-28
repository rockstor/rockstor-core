"""
Copyright (joint work) 2024 The Rockstor Project <https://rockstor.com>

Rockstor is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

Rockstor is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
import random
import string
from hashlib import md5
from pwd import getpwnam
from storageadmin.models import Pincard, EmailClient, User
from system.users import smbpasswd, usermod
from system.email_util import email_root
from django.contrib.auth.models import User as DjangoUser


def reset_password(uname: str, uid: int, pinlist: dict[str]) -> tuple[str, bool]:
    """
    Loop through pinlist, get md5 digest of every pin
    and compare with Pincard model's DB values.
    @param uname: username.
    @param uid: e.g. uid=1022 of type <class 'int'>
    @param pinlist: e.g. {'2': '111', '6': '222', '11': '333', '16': '444'} of type <class 'dict'>
    @return:
    """
    pass_change_enabled = True
    for pin_index, pin_value in pinlist.items():
        pin_value_md5: str = md5(bytes(pin_value, "utf8")).hexdigest()
        if (
            not Pincard.objects.filter(user=uid)
            .filter(pin_number=int(pin_index))
            .filter(pin_code=pin_value_md5)
            .exists()
        ):
            pass_change_enabled = False
            break

    if pass_change_enabled:
        # Generate new 8 chars random password
        new_password: str = "".join(
            random.choice(string.ascii_letters + string.digits) for _ in range(8)
        )
        # Reset system password
        usermod(uname, new_password)

        # If user is a managed one we have to reset smb pass too
        if User.objects.filter(username=uname).exists():
            smbpasswd(uname, new_password)
        # If user is a Django user reset pass
        if DjangoUser.objects.filter(username=uname).exists():
            duser = DjangoUser.objects.get(username=uname)
            duser.set_password(new_password)
            duser.save()

        password_message = (
            f"Password reset succeeded. New password is {new_password} (will not be shown again)."
        )
        password_status = True

    else:
        password_message = "At least one pin was wrong, password reset failed."
        password_status = False

    return password_message, password_status


def reset_random_pins(uid: str):
    """
    Randomly get 4 pins from Pincard for selected user.
    @param uid:
    @return:
    """
    random_pins = random.sample(range(1, 24), 4)
    pin_rows = list(
        Pincard.objects.filter(user=int(uid))
        .filter(pin_number__in=random_pins)
        .values("pin_number")
    )

    return pin_rows


def generate_otp(username: str) -> str:
    """
    Generate a random 6 chars text and sent to root mail
    @param username:
    @return:
    """
    new_otp: str = "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(6)
    )
    otp_subject: str = "Received password reset request for uid 0 user"
    otp_message: str = f"System has received a password reset request for user {username}\n\n OTP string value is: {new_otp}"

    email_root(otp_subject, otp_message)

    return new_otp


def username_to_uid(username: str) -> int | None:
    """
    Convert from username to user uid
    @param username:
    @return:
    """
    try:
        # retrieve the password database entry for a given username
        user_uid = getpwnam(username).pw_uid
    except KeyError:
        # user doesn't exist
        user_uid = None

    return user_uid


def email_notification_enabled() -> bool:
    """
    Check for email notifications state
    required for password reset over root user (Pincard + otp via mail)
    @return:
    """
    try:
        mail_accounts = EmailClient.objects.filter().count()
    except EmailClient.DoesNotExist:
        mail_accounts = 0

    has_mail = True if mail_accounts > 0 else False

    return has_mail


def has_pincard(user: User) -> bool:
    """
    Check if user has already a Pincard
    Added uid_field to dinamically handle passed data:
    user can be and User obcject or directly a uid
    @param user:
    @return:
    """

    uid_field = user.uid if hasattr(user, "uid") else user
    try:
        pins = Pincard.objects.filter(user=int(uid_field)).count()
    except Pincard.DoesNotExist:
        pins = 0

    has_pincard_return: bool = True if (pins == 24) else False

    return has_pincard_return


def pincard_states(user: User) -> tuple[str, bool]:
    """
    If user has a Pincard that means already allowed to have one, so avoid
    computing If selected user is a managed one allowed to have a
    pincard_allowed If user is uid 0 (root) and mail notifications enabled ->
    ok Pincard Otherwise 'otp' third state : allowed to have a Pincard, but
    mail notifications required
    @param user:
    @return:
    """
    pincard_allowed = "no"
    pincard_present = has_pincard(user)
    if user.managed_user:
        pincard_allowed = "yes"
    else:
        if user.uid == 0:
            pincard_allowed = "yes" if email_notification_enabled() else "otp"
        else:
            pincard_allowed = "no"

    return pincard_allowed, pincard_present


def generate_pincard() -> tuple[list[str], list[str]]:
    """
    Generate a 72 chars string over letters, digits, and punctuation.
    Split string in 3 chars groups for 24 total pins and crypt them.
    @return:
    """
    pincard_plain: str = "".join(
        random.choice(string.ascii_letters + string.digits + string.punctuation)
        for _ in range(72)
    )
    pincard_plain_list: list[str] = [
        pincard_plain[i : i + 3] for i in range(0, len(pincard_plain), 3)
    ]
    pincard_crypted: list[str] = []
    for pin in pincard_plain_list:
        pincard_crypted.append(md5(bytes(pin, "utf8")).hexdigest())

    return pincard_plain_list, pincard_crypted


def flush_pincard(uid: int | None):
    """
    Clear all Pincard entries for selected user
    But only if we have an uid, see username_to_uid() which will return None
    if called when the given user no longer exists.
    @param uid:
    @return:
    """
    if uid is not None:
        # Bulk delete all Pincard keys for this user via queryset.
        Pincard.objects.filter(user=uid).delete()


def save_pincard(uid: str) -> list[str]:
    """
    Generate new pincard - plain text for frontend and md5 vals for db
    Flush current pincard over db
    Populate db and return plain text pins to user
    @param uid:
    @return:
    """
    pincard_for_onetime_display, pincard_for_db = generate_pincard()
    flush_pincard(int(uid))

    for index, pin in enumerate(pincard_for_db, start=1):
        newpin = Pincard(user=int(uid), pin_number=index, pin_code=pin)
        newpin.save()

    return pincard_for_onetime_display
