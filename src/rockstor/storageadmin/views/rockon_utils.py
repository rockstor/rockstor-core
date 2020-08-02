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

from system.osi import run_command
import logging

logger = logging.getLogger(__name__)


DOCKER = "/usr/bin/docker"


def container_status(name):
    state = "unknown_error"
    try:
        o, e, rc = run_command(
            [
                DOCKER,
                "inspect",
                "-f",
                "Error:{{.State.Error}},ExitCode:{{.State.ExitCode}},Running:{{.State.Running}}",
                name,
            ]
        )  # noqa E501
        state_d = {}
        for i in o[0].split(","):
            fields = i.split(":")
            if len(fields) >= 2:
                state_d[fields[0]] = ":".join(fields[1:])
        if "Running" in state_d:
            if state_d["Running"] == "true":
                state = "started"
            else:
                state = "stopped"
                if "Error" in state_d and "ExitCode" in state_d:
                    exitcode = int(state_d["ExitCode"])
                    if exitcode != 0:
                        state = "exitcode: %d error: %s" % (exitcode, state_d["Error"])
        return state
    except Exception as e:
        logger.exception(e)
    finally:
        return state
