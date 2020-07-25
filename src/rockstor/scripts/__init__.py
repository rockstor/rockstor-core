import os

os.environ["DJANGO_SETTINGS_MODULE"] = "settings"
import django  # noqa E402

django.setup()
