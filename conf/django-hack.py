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
    join(base, "eggs/URLObject-2.1.1-py2.7.egg"),
    join(base, "eggs/chardet-4.0.0-py2.7.egg"),
    join(base, "eggs/distribute-0.7.3-py2.7.egg"),
    join(base, "eggs/django_braces-1.13.0-py2.7.egg"),
    join(base, "eggs/django_oauth_toolkit-1.1.2-py2.7.egg"),
    join(base, "eggs/django_pipeline-1.6.9-py2.7.egg"),
    join(base, "eggs/huey-2.3.0-py2.7.egg"),
    join(base, "eggs/djangorecipe-2.2.1-py2.7.egg"),
    join(base, "eggs/djangorestframework-3.9.3-py2.7.egg"),
    join(base, "eggs/gevent-1.1.2-py2.7-linux-x86_64.egg"),
    join(base, "eggs/gevent_websocket-0.9.5-py2.7.egg"),
    join(base, "eggs/oauthlib-3.1.0-py2.7.egg"),
    join(base, "eggs/psutil-3.3.0-py2.7-linux-x86_64.egg"),
    join(base, "eggs/psycogreen-1.0-py2.7.egg"),
    join(base, "eggs/psycopg2-2.7.4-py2.7-linux-x86_64.egg"),
    join(base, "eggs/python_engineio-2.3.2-py2.7.egg"),
    join(base, "eggs/python_socketio-1.6.0-py2.7.egg"),
    join(base, "eggs/pytz-2014.3-py2.7.egg"),
    join(base, "eggs/pytz-2021.1-py2.7.egg"),
    join(base, "eggs/pyzmq-15.0.0-py2.7-linux-x86_64.egg"),
    join(base, "eggs/requests-2.25.1-py2.7.egg"),
    join(base, "src"),
    join(base, "src/rockstor"),
]


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.py")
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
