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

# to be moved to views/email_client.py after an update or so.

import smtplib
# https://docs.python.org/3.6/library/email.mime.html
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from system.osi import gethostname


def test_smtp_auth(eco):
    auth = None
    try:
        smtp = smtplib.SMTP(eco.get("smtp_server"), eco.get("port"))
    except:
        return False
    smtp.ehlo()
    smtp.starttls()
    try:
        smtp.login(eco.get("username"), eco.get("password"))
        auth = True
    except:
        auth = False
    finally:
        smtp.close()
        return auth


def send_test_email(eco, subject):
    msg = MIMEMultipart()
    msg["From"] = eco.sender
    msg["To"] = eco.receiver
    msg["Date"] = formatdate(localtime=True)
    msg["Subject"] = subject

    msg.attach(MIMEText(subject))
    smtp = smtplib.SMTP("localhost")
    smtp.sendmail(eco.sender, eco.receiver, msg.as_string())
    smtp.close()


def email_root(subject, message):
    """
    Simple wrapper to email root, which generally will be forwarded to admin
    personnel if email notifications are enabled hence acting as remote monitor
    / notification system
    :param subject: of the email
    :param message: body content of the email
    """
    hostname = gethostname()

    msg = MIMEMultipart()
    msg["From"] = "notifications@%s" % hostname
    msg["To"] = "root@%s" % hostname
    msg["Date"] = formatdate(localtime=True)
    msg["Subject"] = subject
    msg.attach(MIMEText(message))

    smtp = smtplib.SMTP("localhost")
    smtp.sendmail(msg["From"], msg["To"], msg.as_string())
    smtp.close()
