"""
Copyright (c) 2023 RockStor, Inc. <https://rockstor.com>
This file is part of RockStor.

RockStor is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 3 of the License,
or (at your option) any later version.

RockStor is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.

"""

# Django settings for Rockstor project.
import os
import distro
import secrets
from huey import SqliteHuey

# By default, DEBUG = False, honour this by True only if env var == "True"
DEBUG = os.environ.get("DJANGO_DEBUG", "") == "True"

ALLOWED_HOSTS = [
    "*",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "storageadmin",  # Or path to database file if using sqlite3.
        "USER": "rocky",  # Not used with sqlite3.
        "PASSWORD": "rocky",  # Not used with sqlite3.
        "HOST": "",  # Set to empty string for localhost. Not used with sqlite3.
        "PORT": "",  # Set to empty string for default. Not used with sqlite3.
    },
    "smart_manager": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "smartdb",
        "USER": "rocky",
        "PASSWORD": "rocky",
        "HOST": "",
        "PORT": "",
    },
}

DATABASE_ROUTERS = [
    "smart_manager.db_router.SmartManagerDBRouter",
]

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = "Europe/Lisbon"

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = "en-us"

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = "static"

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = "/static/"

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = "/media/"

# Establish BASE_DIR from ourselves (./src/rockstor/settings.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# print("BASE_DIR={}".format(BASE_DIR))  # "/opt/rockstor" via 'django-admin runserver'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "static")

# Absolute filesystem path where config backups are stored by default
DEFAULT_CB_DIR = os.path.join(MEDIA_ROOT, "config-backups")

# Additional locations of static files
STATICFILES_DIRS = (os.path.join(BASE_DIR, "jslibs"),)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "django.contrib.staticfiles.finders.FileSystemFinder",
    # https://django-pipeline.readthedocs.io/en/latest/installation.html
    "pipeline.finders.PipelineFinder",
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = "odk7(t)1y$ls)euj3$2xs7e^i=a9b&amp;xtf&amp;z=-2bz$687&amp;^q0+3"

# API client secret
CLIENT_SECRET = secrets.token_urlsafe()

# New in Django 1.8 to cover all prior TEMPLATE_* settings.
# https://docs.djangoproject.com/en/1.11/ref/templates/upgrading/
# "All existing template related settings were deprecated."
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            # insert your TEMPLATE_DIRS here
            "{}/src/rockstor/storageadmin/templates/storageadmin".format(BASE_DIR),
            "{}/src/rockstor/templates/admin".format(BASE_DIR),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ],
        },
    },
]

MIDDLEWARE = (
    # New in 1.8, 1.11 newly sets Content-Length header.
    # 'django.middleware.common.CommonMiddleware',
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "storageadmin.middleware.ProdExceptionMiddleware",
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

# Relates to django.middleware.common.CommonMiddleware
# https://docs.djangoproject.com/en/3.2/ref/middleware/#module-django.middleware.common
# Default changed to True between 1.8 and 1.11, breaking may POST urls we have in play.
# APPEND_SLASH = False

ROOT_URLCONF = "urls"

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = "wsgi.application"

INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Uncomment the next line to enable the admin:
    "django.contrib.admin",
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    "storageadmin",
    "pipeline",
    "rest_framework",
    "smart_manager",
    "oauth2_provider",
    "huey.contrib.djhuey",
)

STATICFILES_STORAGE = "pipeline.storage.PipelineManifestStorage"

# Have django-pipeline collate storageadmin js/jst files into one storageadmin.js file
# which is then referenced in setup.html and base.html templates.
PIPELINE = {
    "DISABLE_WRAPPER": True,
    "JS_COMPRESSOR": None,
    "CSS_COMPRESSOR": None,
    "TEMPLATE_FUNC": "Handlebars.compile",
    "JAVASCRIPT": {
        "storageadmin": {
            "source_filenames": (
                "storageadmin/js/license.js",
                "storageadmin/js/templates/**/*.jst",
                "storageadmin/js/templates/**/**/*.jst",
                "storageadmin/js/socket_listen.js",
                "storageadmin/js/rockstor.js",
                "storageadmin/js/rockstor_widgets.js",
                "storageadmin/js/rockstor_logger.js",
                "storageadmin/js/paginated_collection.js",
                "storageadmin/js/router.js",
                "storageadmin/js/graph.js",
                "storageadmin/js/d3.slider2.js",
                "storageadmin/js/models/models.js",
                "storageadmin/js/views/common/*.js",
                "storageadmin/js/views/*.js",
                "storageadmin/js/views/pool/**/*.js",
                "storageadmin/js/views/dashboard/*.js",
            ),
            "output_filename": "storageadmin/js/storageadmin.js",
        },
    },
}

# A sample logging configuration. The only tangible logging
# performed by this configuration is to email
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOG_LEVEL = "DEBUG" if DEBUG else "INFO"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {
        "standard": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
    },
    "handlers": {
        "mail_admins": {
            "level": "DEBUG",
            # 'filters': ['require_debug_false'],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "file": {
            "level": LOG_LEVEL,
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "{}/var/log/rockstor.log".format(BASE_DIR),
            "maxBytes": 1000000,
            "backupCount": 3,
            "formatter": "standard",
        },
    },
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
        "storageadmin": {
            "handlers": ["file"],
            "level": LOG_LEVEL,
            "propagate": True,
        },
        "smart_manager": {
            "handlers": ["file"],
            "level": LOG_LEVEL,
            "propagate": True,
        },
        "system": {
            "handlers": ["file"],
            "level": LOG_LEVEL,
            "propagate": True,
        },
        "scripts": {
            "handlers": ["file"],
            "level": LOG_LEVEL,
            "propagate": True,
        },
        "fs": {
            "handlers": ["file"],
            "level": LOG_LEVEL,
            "propagate": True,
        },
    },
}

MNT_PT = "/mnt2/"
NFS_EXPORT_ROOT = "/export/"
SFTP_MNT_ROOT = "/mnt3/"

# System volume label when no btrfs volume label is set as per default openSUSE
# install: ie 'btrfs fi show' gives 'Label: none'
SYS_VOL_LABEL = "ROOT"

TAP_DIR = "{}/src/rockstor/smart_manager/taplib".format(BASE_DIR)
TAP_SERVER = ("127.0.0.1", 10000)
MAX_TAP_WORKERS = 10
SPROBE_SINK = ("127.0.0.1", 10001)

SUPPORT = {
    "email": "suman@rockstor.com",
    "log_loc": "{}/var/log".format(BASE_DIR),
}

"""
Maximum number of seconds to keep data collected by smart probes. The logic
behind this needs to evolve quite a bit.
"""
PROBE_DATA_INTERVAL = 600

"""
Minimum share size allowed is 100KB. This is purely arbitrary. 4K is what is
strictly required by btrfs. Similarly the maximum is 2^64 bytes which is more than
enough for all practical purposes and also is the max allowed in btrfs.
"""
MIN_SHARE_SIZE = 100
MAX_SHARE_SIZE = 18014398509481984

START_UID = 5000
END_UID = 6000
VALID_SHELLS = (
    "{}/bin/rcli".format(BASE_DIR),
    "/bin/bash",
    "/sbin/nologin",
)

SCHEDULER = ("127.0.0.1", 10001)
REPLICATION = {
    "ipc_socket": "/var/run/replication.sock",
    "max_send_attempts": 10,
    "max_snap_retain": 2,
    "listener_port": 10002,
}

SHARE_REGEX = r"[A-Za-z0-9_.-]+"
POOL_REGEX = SHARE_REGEX
USERNAME_REGEX = r"[A-Za-z][-a-zA-Z0-9_]*$"
ROOT_DIR = BASE_DIR + "/"

# things get purged when they are > MAX_TS_RECORDS x MAX_TS_MULTIPLIER of if the service just
# starts, and they are > MAX_TS_RECORDS.
MAX_TS_RECORDS = 40000
MAX_TS_MULTIPLIER = 3

# various system binaries used by lower level code.
COMMANDS = {
    "ntpdate": "/usr/sbin/ntpdate",
    "systemctl": "/usr/bin/systemctl",
}

SYSCONFIG = {
    "ntp": "/etc/ntp.conf",
}

SOUTH_TESTS_MIGRATE = False

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework_custom.custom_pagination.CustomPagination",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "PAGE_SIZE": 15,
    "MAX_LIMIT": 10000,
}

CONFROOT = "{}/conf".format(BASE_DIR)
CERTDIR = "{}/certs".format(BASE_DIR)
COMPRESSION_TYPES = (
    "zlib",
    "lzo",
    "zstd",
    "no",
)

SNAP_TS_FORMAT = "%Y%m%d%H%M"

MODEL_DEFS = {
    "pqgroup": "-1/-1",
}

OAUTH2_PROVIDER = {
    "PKCE_REQUIRED": False,
}

OAUTH_INTERNAL_APP = "cliapp"
OAUTH2_PROVIDER_APPLICATION_MODEL = "oauth2_provider.Application"

# Header string to separate auto config options from rest of config file.
# this could be generalized across all Rockstor config files, problems during
# upgrades though
NUT_HEADER = "###BEGIN: Rockstor NUT Config. DO NOT EDIT BELOW THIS LINE###"

# The ip address for the LISTEN directive in upsd.conf when in netserver mode
# when set to 0.0.0.0 it will accept connections from any machine.
# default port is 3493
# Note this might later be tied into multi lan configs ie ups monitoring on
# admin interface for example.
NUT_LISTEN_ON_IP = "0.0.0.0"

# The command that the root part of upsmon uses to shut down the system.
NUT_SYSTEM_SHUTDOWNCMD = "/sbin/shutdown -h +0"

# Shell In A Box base settings
if distro.id() == "rockstor":
    SHELLINABOX = {
        "user": "shellinabox",
        "group": "shellinabox",
        "port": "4200",
        "certs": "/var/lib/shellinabox",
    }
else:
    SHELLINABOX = {
        "user": "shellinabox",
        "group": "shellinabox",
        "port": "4200",
        "certs": "/etc/shellinabox/certs",
    }

UPDATE_CHANNELS = {
    "stable": {
        "name": "Stable",
        "description": "Subscription channel for stable updates",
        "url": "updates.rockstor.com:8999/rockstor-stable",
    },
    "testing": {
        "name": "Testing",
        "description": "Subscription channel for testing updates",
        "url": "updates.rockstor.com:8999/rockstor-testing",
    },
}

HUEY = SqliteHuey(filename="{}/rockstor-tasks-huey.db".format(BASE_DIR))

TASK_SCHEDULER = {"max_log": 100}  # max number of task log entries to keep

# Establish our OS base id, name, and version:
# Use id for code path decisions. Others are for Web-UI display purposes.
# Examples given are for CentOS Rockstor variant, Leap 15, and Tumblweed.
OS_DISTRO_ID = distro.id()  # rockstor, opensuse-leap/opensuse, opensuse-tumbleweed
OS_DISTRO_NAME = distro.name()  # Rockstor, openSUSE Leap, openSUSE Tumbleweed
# Note that the following will capture the build os version.
# For live updates (running system) we call distro.version() directly in code.
OS_DISTRO_VERSION = distro.version()  # 3, 15.0 ,20181107
