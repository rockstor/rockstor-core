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
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

from settings import DATABASES


class SmartManagerDBRouter(object):
    app = "smart_manager"
    database = app  # settings.DATABASES reference == app_label in settings.INSTALLED_APPS

    @staticmethod
    def _db_unknown(dbase):
        if dbase not in DATABASES:
            return None

    def db_for_read(self, model, **hints):
        self._db_unknown(self.database)

        if model._meta.app_label == self.app:
            return self.database
        return None

    def db_for_write(self, model, **hints):
        self._db_unknown(self.database)

        if model._meta.app_label == self.app:
            return self.database
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        https://docs.djangoproject.com/en/4.0/topics/db/multi-db/#allow_relation
        "If no router has an opinion (i.e. all routers return None),
        only relations within the same database are allowed."
        """
        # N.B. smart_manager.task_def @property "pool_name" retrieves a storageadmin.Pool
        # instance to retrieve Pool.name and validate task_metadata["pool"] against Pool.id.
        # But this is not a ForeignKey model-to-model inter db relationship.
        # Ensure we avoid inter db relations.
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        self._db_unknown(self.database)

        if app_label == self.app:
            # Migrate (True) for our target db, we are called for all databases.
            return db == self.database
        else:  # For non self.app_label models, migrate (True) if database is default
            return db == "default"
