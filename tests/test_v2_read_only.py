import httpx
import pytest
import respx

from gns3_mcp.client import GNS3Client
from gns3_mcp.config import Settings
from gns3_mcp.console import validate_read_only_command


BASE = "http://gns3.test:3080"


@pytest.mark.asyncio
@respx.mock
async def test_v2_uses_basic_auth_without_login_endpoint():
    route = respx.get(f"{BASE}/v2/version").mock(
        return_value=httpx.Response(200, json={"version": "2.2.50"})
    )
    client = GNS3Client(
        Settings(
            base_url=BASE,
            api_version="v2",
            username="admin",
            password="secret",
            read_only=True,
        )
    )

    assert await client.get("/version") == {"version": "2.2.50"}
    assert route.calls.last.request.headers["authorization"].startswith("Basic ")
    assert not respx.calls.call_count > 1
    await client.aclose()


def test_v2_settings_are_read_only_and_use_v2_prefix():
    settings = Settings(
        base_url=BASE,
        api_version="v2",
        username="admin",
        password="secret",
    )

    assert settings.api_base == f"{BASE}/v2"
    assert settings.read_only is True


@pytest.mark.asyncio
async def test_v2_server_registers_no_mutating_tools(monkeypatch):
    monkeypatch.setenv("GNS3_API_VERSION", "v2")
    monkeypatch.setenv("GNS3_BASE_URL", BASE)
    monkeypatch.setenv("GNS3_USERNAME", "admin")
    monkeypatch.setenv("GNS3_PASSWORD", "secret")

    import inspect

    import gns3_mcp.runtime as runtime
    from gns3_mcp.server import build_server

    runtime._client = None
    runtime._settings = None
    server = build_server()
    tools = server.get_tools()
    tools = await tools if inspect.isawaitable(tools) else tools

    assert "projects_list" in tools
    assert "node_console_diagnostic" in tools
    assert "project_create" not in tools
    assert "node_start" not in tools
    assert "capture_start" not in tools
    assert "access_user_create" not in tools
    await runtime.shutdown()


@pytest.mark.asyncio
@respx.mock
async def test_v2_statistics_preserves_list_shape_through_mcp(monkeypatch):
    monkeypatch.setenv("GNS3_API_VERSION", "v2")
    monkeypatch.setenv("GNS3_BASE_URL", BASE)
    monkeypatch.setenv("GNS3_USERNAME", "admin")
    monkeypatch.setenv("GNS3_PASSWORD", "secret")
    respx.get(f"{BASE}/v2/statistics").mock(
        return_value=httpx.Response(200, json=[{"compute_id": "local", "statistics": {}}])
    )

    import gns3_mcp.runtime as runtime
    from fastmcp import Client
    from gns3_mcp.server import build_server

    runtime._client = None
    runtime._settings = None
    server = build_server()
    async with Client(server) as client:
        result = await client.call_tool("gns3_statistics")
    await runtime.shutdown()

    assert "compute_id" in result.content[0].text


@pytest.mark.parametrize(
    "command",
    ["show ip route", "show running-config | include ospf", "ping 10.10.50.20"],
)
def test_read_only_console_allows_diagnostic_commands(command):
    assert validate_read_only_command(command) == command


@pytest.mark.parametrize(
    "command",
    ["conf t", "interface Gi0/1", "reload", "write memory", "no shutdown"],
)
def test_read_only_console_rejects_configuration_commands(command):
    with pytest.raises(ValueError):
        validate_read_only_command(command)
