#!/usr/bin/python2.7

"""Django's command-line utility for administrative tasks."""
# Based on a pre Python 3 version of:
# https://github.com/django/django/blob/main/django/conf/project_template/manage.py-tpl
# see also:
# https://github.com/django/django/tree/main/django/conf/project_template/project_name
import os
import sys

join = os.path.join
base = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
base = os.path.dirname(base)

sys.path[0:0] = [
    base,
    join(base, "eggs/Django-1.11.29-py2.7.egg"),
    join(base, "eggs/URLObject-2.1.1-py2.7-linux-x86_64.egg"),
    join(base, "eggs/URLObject-2.1.1-py2.7-linux-aarch64.egg"),
    join(base, "eggs/URLObject-2.1.1-py2.7.egg"),  # remove when 15.3 eol
    join(base, "eggs/chardet-4.0.0-py2.7.egg"),
    # join(base, "eggs/distribute-0.7.3-py2.7.egg"),
    join(base, "eggs/django_braces-1.13.0-py2.7.egg"),
    join(base, "eggs/django_oauth_toolkit-1.1.2-py2.7.egg"),
    join(base, "eggs/django_pipeline-1.6.9-py2.7.egg"),
    join(base, "eggs/huey-2.3.0-py2.7-linux-x86_64.egg"),
    join(base, "eggs/huey-2.3.0-py2.7-linux-aarch64.egg"),
    join(base, "eggs/huey-2.3.0-py2.7.egg"),  # remove when 15.3 eol
    join(base, "eggs/djangorecipe-2.2.1-py2.7-linux-x86_64.egg"),
    join(base, "eggs/djangorecipe-2.2.1-py2.7-linux-aarch64.egg"),
    join(base, "eggs/djangorecipe-2.2.1-py2.7.egg"),  # remove when 15.3 eol
    join(base, "eggs/djangorestframework-3.9.3-py2.7.egg"),
    join(base, "eggs/gevent-1.1.2-py2.7-linux-x86_64.egg"),
    join(base, "eggs/gevent-1.1.2-py2.7-linux-aarch64.egg"),
    join(base, "eggs/gevent_websocket-0.9.5-py2.7-linux-x86_64.egg"),
    join(base, "eggs/gevent_websocket-0.9.5-py2.7-linux-aarch64.egg"),
    join(base, "eggs/gevent_websocket-0.9.5-py2.7.egg"),  # remove when 15.3 eol
    join(base, "eggs/oauthlib-3.1.0-py2.7.egg"),
    join(base, "eggs/psutil-5.9.4-py2.7-linux-x86_64.egg"),
    join(base, "eggs/psutil-5.9.4-py2.7-linux-aarch64.egg"),
    join(base, "eggs/psycogreen-1.0-py2.7-linux-x86_64.egg"),
    join(base, "eggs/psycogreen-1.0-py2.7-linux-aarch64.egg"),
    join(base, "eggs/psycogreen-1.0-py2.7.egg"),  # remove when 15.3 eol
    join(base, "eggs/psycopg2-2.8.6-py2.7-linux-x86_64.egg"),
    join(base, "eggs/psycopg2-2.8.6-py2.7-linux-aarch64.egg"),
    join(base, "eggs/python_engineio-2.3.2-py2.7.egg"),
    join(base, "eggs/python_socketio-1.6.0-py2.7-linux-x86_64.egg"),
    join(base, "eggs/python_socketio-1.6.0-py2.7-linux-aarch64.egg"),
    join(base, "eggs/python_socketio-1.6.0-py2.7.egg"),  # remove when 15.3 eol
    join(base, "eggs/pytz-2022.6-py2.7.egg"),
    join(base, "eggs/pyzmq-19.0.2-py2.7-linux-x86_64.egg"),
    join(base, "eggs/pyzmq-19.0.2-py2.7-linux-aarch64.egg"),
    join(base, "eggs/urllib3-1.26.12-py2.7.egg"),
    join(base, "eggs/idna-2.10-py2.7.egg"),
    join(base, "eggs/certifi-2021.10.8-py2.7.egg"),
    join(base, "eggs/requests-2.27.1-py2.7.egg"),
    join(base, "eggs/dbus_python-1.2.18-py2.7-linux-x86_64.egg"),
    join(base, "eggs/dbus_python-1.2.18-py2.7-linux-aarch64.egg"),
    join(base, "eggs/distro-1.6.0-py2.7.egg"),
    join(base, "eggs/six-1.16.0-py2.7.egg"),
    join(base, "src"),
    join(base, "src/rockstor"),
]


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
