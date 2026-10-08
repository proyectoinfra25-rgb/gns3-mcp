#!/usr/bin/env python3
"""Launch the local read-only v2 MCP using the user's GNS3 server config.

The password is read at runtime and never printed or written by this helper.
Override GNS3_CONFIG_FILE when the controller config lives elsewhere.
"""

from __future__ import annotations

import configparser
import os
from pathlib import Path
import shutil
import sys


def main() -> int:
    config_path = Path(
        os.environ.get(
            "GNS3_CONFIG_FILE",
            Path.home() / ".config" / "GNS3" / "2.2" / "gns3_server.conf",
        )
    )
    parser = configparser.ConfigParser()
    if not parser.read(config_path) or not parser.has_section("Server"):
        raise SystemExit(f"GNS3 server config not found: {config_path}")

    server = parser["Server"]
    for key in ("host", "port", "user", "password"):
        if not server.get(key, "").strip():
            raise SystemExit(f"Missing Server.{key} in {config_path}")

    environment = os.environ.copy()
    environment.update(
        {
            "GNS3_API_VERSION": "v2",
            "GNS3_READ_ONLY": "true",
            "GNS3_BASE_URL": f"{server.get('protocol', 'http')}://{server['host']}:{server['port']}",
            "GNS3_USERNAME": server["user"],
            "GNS3_PASSWORD": server["password"],
        }
    )
    command = shutil.which("gns3-mcp")
    if command is None:
        raise SystemExit("gns3-mcp is not installed in the active environment")
    os.execvpe(command, [command], environment)
    return 0


if __name__ == "__main__":
    sys.exit(main())
