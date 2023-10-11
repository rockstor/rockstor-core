"""
Copyright (c) 2012-2023 RockStor, Inc. <https://rockstor.com>
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
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
import logging
import re
import time
from typing import List

from storageadmin.exceptions import RockStorAPIException
from system.constants import TAILSCALE
from system.network import enable_ip_forwarding, disable_ip_forwarding

from system.osi import run_command
from system.services import get_tailscale_status

# Config options supported in webUI
# (used to filter out eventual duplicates in ts_custom_config)
TS_UI_SETTINGS = [
    "accept_routes",
    "advertise_exit_node",
    "advertise_routes",
    "exit_node",
    "exit_node_allow_lan_access",
    "hostname",
    "reset",
    "ssh",
]
logger = logging.getLogger(__name__)


def tailscale_up(config: dict = None, timeout: int = None):
    """Start tailscale
    Wrapper around `tailscale up`. It first gets args from config (if any)
    and constructs the tailscale up command accordingly.
    Adds the timeout flag is specified (used to generate authURL during the
    LOGIN action from the webUI).
    """
    # Construct tailscale up command
    cmd = [
        TAILSCALE,
        "up",
    ]
    if config is not None:
        cmd = construct_tailscale_up_command(config)
        # Enable IP forwarding if needed (subnet router or exit node enabled)
        if any(key in config for key in ("advertise_exit_node", "advertise_routes")):
            enable_ip_forwarding(name="tailscale", priority=99)
    # Add short timeout to just trigger the creation of authURL
    if timeout:
        cmd.append(f"--timeout={timeout}s")
    return run_command(cmd, log=True, throw=False)


def tailscale_down(config: dict = None):
    """Stop tailscale
    Wrapper around `tailscale down`.
    """
    cmd = [
        TAILSCALE,
        "down",
    ]
    o, e, rc = run_command(cmd, log=True, throw=False)
    if config is not None:
        if any(key in config for key in ("advertise_exit_node", "advertise_routes")):
            disable_ip_forwarding(name="tailscale")
    return o, e, rc


def extract_param(param: str) -> str:
    """Get and format the name of a custom parameter
    Isolates the name of the parameter from its cli format and
    returns it after brief formatting.

    There are 2 types of params:
      - in the form --<key>=<value>
      - in the form --<key>

    These would return, for instance:
      - "--accept-risk=all" -> "accept_risk"
      - "--shields-up" -> "shields_up"
    """
    if re.search("=", param) is not None:
        param = param.split("=")[0]
    param = param.split("--")[1]

    # Tailscale cli params use "-" whereas Rockstor uses "_" for storage
    param = re.sub("-", "_", param)

    return param


def validate_ts_hostname(config: dict) -> dict:
    """Ensure hostname is alphanumeric with hyphens only
    No special character (including hyphens) is allowed as a custom hostname.

    "hostname": "rock-dev_@#~!$%^&*()+123"
    should return
    "hostname": "rock-dev-123"
    """
    if "hostname" in config:
        config["hostname"] = re.sub("_", "-", config["hostname"])
        to_exclude = [
            "@",
            "#",
            "~",
            "!",
            "$",
            "%",
            "^",
            "&",
            "*",
            "(",
            ")",
            "+",
        ]
        config["hostname"] = "".join(
            c for c in config["hostname"] if not c in to_exclude
        )
    return config


def validate_ts_custom_config(custom_config: List) -> List:
    """Validate Tailscale service custom config
    Check for the existence of duplicates in the custom config section
    and filter them out if any.

    :param custom_config: list of parsed custom config
    :return: list of filtered custom config
    """
    # Keep only param in the form '--<param>'
    custom_config = [x for x in custom_config if re.match("--", x)]
    # Keep only settings not already in UI modal
    filtered_conf = [
        setting
        for setting in custom_config
        if extract_param(setting) not in TS_UI_SETTINGS
    ]
    return filtered_conf


def construct_tailscale_up_command(config: dict) -> List:
    """Construct the tailscale up command from service config"""
    yes_flags = ["yes", "true"]
    cmd = [
        TAILSCALE,
        "up",
    ]
    for param in config:
        if param == "auth_url":
            # do not add auth_url to cmd as it is not valid
            continue
        elif param == "custom_config":
            for flag in config[param]:
                cmd.append(flag)
        elif config[param] in yes_flags:
            cmd.append("--" + re.sub("_", "-", param))
        else:
            formatted_key = re.sub("_", "-", param)
            cmd.append(f"--{formatted_key}={config[param]}")
    return cmd


def get_ts_auth_url() -> str:
    """Get AuthURL from tailscale status output
    Query the json output from `tailscale status --json`
    to get the generated AuthURL. Repeat every sec for 10 sec or raise
    a RockstorAPIException.
    """
    cur_wait = 0
    while True:
        logger.debug(f"Attempt number {cur_wait} to get AUTH_URL")
        ts_status = get_tailscale_status()
        auth_url = ts_status["AuthURL"]
        if len(auth_url) > 0:
            break
        if cur_wait > 10:
            logger.error(
                f"Waited too long ({cur_wait} seconds) for tailscale "
                "to generate login URL... giving up."
            )
            # break
            e_msg = (
                f"Waited too long ({cur_wait} seconds) for tailscale to generate the login URL. "
                "Please try again. If the problem persists, email support@rockstor.com "
                "with this message, or inquire on our forum (https://forum.rockstor.com)."
            )
            raise RockStorAPIException(status_code=400, detail=e_msg)
        time.sleep(1)
        cur_wait += 1
    return auth_url
