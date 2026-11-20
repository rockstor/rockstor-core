"""
Copyright (joint work) 2026 The Rockstor Project <https://rockstor.com>

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

from settings import ROOT_DIR

"""This module defines smart_manager level constants."""
"""Take care to minimise import in this module, to guard against circular dependency."""

# Used by TaskDefinition.task_type field choices directive.
# https://docs.djangoproject.com/en/6.1/ref/models/fields/#choices
# {TaskDefinition.task_type-value: Human-display/label}
# Top level is task group pertaining to the task target, shown but unselectable by
# choices directive.
TASK_TYPES = {
    "pool": {
        "scrub": "Scrub",
    },
    "share": {
        "snapshot": "Snapshot",
    },
    "power": {
        "reboot": "Reboot",
        "shutdown": "Shutdown",
        "suspend": "Suspend",
    },
    "custom": "Custom",
}

TASK_SCRIPTS = {
    "scrub": f"{ROOT_DIR}.venv/bin/st-pool-scrub",
    "snapshot": f"{ROOT_DIR}.venv/bin/st-snapshot",
    "power": f"{ROOT_DIR}.venv/bin/st-system-power",
    "custom": "",
}

CRONTAB_FILE = "/etc/cron.d/rockstortab"
