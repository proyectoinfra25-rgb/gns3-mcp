"""FastMCP server entry point for the read-only GNS3 controller MCP.

Registers every tool module, MCP resources, and prompts, then runs the selected
transport (stdio by default, streamable-HTTP when GNS3_TRANSPORT=http).
"""

from __future__ import annotations

from fastmcp import FastMCP

from . import resources
from .runtime import init_runtime
from .tools import (
    access,
    appliances,
    capture,
    computes,
    console,
    controller,
    drawings,
    images,
    links,
    nodes,
    pools,
    projects,
    snapshots,
    templates,
)

_TOOL_MODULES = [
    controller,
    projects,
    nodes,
    links,
    drawings,
    snapshots,
    templates,
    computes,
    images,
    appliances,
    pools,
    access,
    console,
    capture,
]

# GNS3 2.2 exposes a smaller, older API surface. Keep this fork deliberately
# narrow for v2: inspection plus safe diagnostic console commands only.
_V2_READ_ONLY_MODULES = [
    controller,
    projects,
    nodes,
    links,
    computes,
    templates,
    console,
]


def build_server() -> FastMCP:
    """Construct the FastMCP app with runtime initialised and all modules registered."""
    settings = init_runtime()
    mcp = FastMCP(
        name="gns3",
        instructions=(
            "Read-only tools for inspecting a GNS3 network-emulation controller: projects, "
            "nodes, links, computes, topology details, and allowlisted show/ping/traceroute "
            "commands over node consoles. Do not attempt configuration or lifecycle changes."
        ),
    )
    modules = _V2_READ_ONLY_MODULES if settings.api_version == "v2" else _TOOL_MODULES
    for module in modules:
        module.register(mcp)
    resources.register(mcp)

    if settings.read_only:
        mcp.instructions += " (Server is in READ-ONLY mode; mutating tools are disabled.)"
    return mcp


def main() -> None:
    """Console-script entry point."""
    from .runtime import get_runtime_settings

    mcp = build_server()
    settings = get_runtime_settings()
    if settings.transport == "http":
        mcp.run(transport="http", host=settings.http_host, port=settings.http_port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
