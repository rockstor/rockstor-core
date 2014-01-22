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

# Django settings for RockStor project.
import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Suman Chakravartula', 'schakrava@gmail.com'),
)

MANAGERS = ADMINS

cur_dirname = os.path.dirname(__file__)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': cur_dirname + '/datastore',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    },
    'smart_manager': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': cur_dirname + '/smartdb',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        },
}

DATABASE_ROUTERS = ['smart_manager.db_router.SmartManagerDBRouter',]

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    cur_dirname + '/templates/storageadmin/js',
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'odk7(t)1y$ls)euj3$2xs7e^i=a9b&amp;xtf&amp;z=-2bz$687&amp;^q0+3'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    cur_dirname + '/templates/storageadmin/',
    cur_dirname + '/templates/admin/',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'storageadmin',
    'pipeline',
    'rest_framework',
    'smart_manager',
)

STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

PIPELINE_CSS_COMPRESSOR = None
PIPELINE_JS_COMPRESSOR = None

PIPELINE_JS = {
    'application': {
        'source_filenames': (
            'js/templates/**/*.jst',
            'js/templates/**/**/*.jst',
            'js/rockstor.js',
            'js/rockstor_logger.js',
            'js/graph.js',
            'js/models/models.js',
            'js/views/appliances.js',
            'js/views/disks_table.js',
            'js/views/disks.js',
            'js/views/disk_detail.js',
            'js/views/pools_table.js',
            'js/views/pools.js',
            'js/views/pool_detail.js',
            'js/views/pool_details_layout_view.js',
            'js/views/pool_info_module.js',
            'js/views/pool_usage_module.js',
            'js/views/add_pool.js',
            'js/views/shares_table.js',
            'js/views/shares.js',
            'js/views/share_detail.js',
            'js/views/share_details_layout_view.js',
            'js/views/share_info_module.js',
            'js/views/share_usage_module.js',
            'js/views/add_share.js',
            'js/views/nfs_exports_table.js',
            'js/views/nfs_exports_table_row.js',
            'js/views/smb_shares.js',
            'js/views/iscsi_target.js',
            'js/views/home.js',
            'js/views/sysinfo_module.js',
            'js/views/cpuusage_module.js',
            'js/views/snapshots_table.js',
            'js/views/setup.js',
            'js/views/setup_users.js',
            'js/views/setup_disks.js',
            'js/views/setup_system.js',
            'js/views/services.js',
            'js/views/dashboard_config.js',
            'js/views/dashboard/sysinfo_widget.js',
            'js/router.js',
            'js/socket_listen.js',
            'js/views/support_table.js',
            'js/views/support.js',
            'js/views/support_case_detail.js',
            'js/views/add_support_case.js',
            'js/views/support_case_details_layout_view.js',
            'js/views/backup.js',
            'js/views/add_backup_policy.js',
            ),
        'output_filename': 'js/application.js'
        },
    }


# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'standard': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
            },
        },
    'handlers': {
        'mail_admins': {
            'level': 'DEBUG',
            #'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/tmp/rockstor.log',
            'maxBytes': 1000000,
            'backupCount': 3,
            'formatter': 'standard',
            },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'storageadmin': {
            'handlers': ['file'],
            'level': 'DEBUG',
            },
        'smart_manager': {
            'handlers': ['file'],
            'level': 'DEBUG',
            },
    }
}

TEMPLATE_CONTEXT_PROCESSORS = (
   "django.contrib.auth.context_processors.auth",
   "django.core.context_processors.debug",
   "django.core.context_processors.i18n",
   "django.core.context_processors.media",
   "django.core.context_processors.static",
   "django.core.context_processors.tz",
   "django.contrib.messages.context_processors.messages",
   "django.core.context_processors.request"
)

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https',)

