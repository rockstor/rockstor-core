"""
Copyright (c) 2012-2020 RockStor, Inc. <http://rockstor.com>
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

APP_LABEL = "smart_manager"


class SmartManagerDBRouter(object):
    def db_for_read(self, model, **hints):
        from django.conf import settings

        if APP_LABEL not in settings.DATABASES:
            return None
        if model._meta.app_label == APP_LABEL:
            return APP_LABEL
        return None

    def db_for_write(self, model, **hints):
        from django.conf import settings

        if APP_LABEL not in settings.DATABASES:
            return None
        if model._meta.app_label == APP_LABEL:
            return APP_LABEL
        return None

    def allow_relation(self, obj1, obj2, **hints):
        from django.conf import settings

        if APP_LABEL not in settings.DATABASES:
            return None
        if obj1._meta.app_label == APP_LABEL or obj2._meta.app_label == APP_LABEL:
            return True
        return None

    def allow_migrate(self, db, model):
        from django.conf import settings

        if APP_LABEL not in settings.DATABASES:
            return None
        if db == APP_LABEL:
            return model._meta.app_label == APP_LABEL
        elif model._meta.app_label == APP_LABEL:
            return False
        return None
