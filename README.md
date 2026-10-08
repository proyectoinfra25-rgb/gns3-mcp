# GNS3 MCP — v2 read-only fork

An MCP server for inspecting a GNS3 2.2 controller through its `/v2` REST API.
This fork is intentionally read-only: it does not create, delete, start, stop,
configure, snapshot, capture, or modify GNS3 resources.

It is designed for topology audits and troubleshooting of an existing lab. The
only console access exposed is an allowlist of diagnostic commands beginning
with `show`, `ping`, `traceroute`, or `traceroute6`; configuration-mode and
shell-like commands are rejected before reaching the device.

## Exposed capabilities

- Controller version and statistics.
- Projects and project statistics.
- Nodes, node details, links, computes, and templates.
- Console information for a node.
- Safe diagnostic console commands through `node_console_diagnostic`.
- MCP resources for the read-only topology views supported by the selected API.

The v2 profile registers only the modules above. The upstream v3 write-capable
surface is not part of this fork's v2 runtime.

## Configuration

| Variable | Required | Purpose |
| --- | --- | --- |
| `GNS3_BASE_URL` | yes | Controller URL, for example `http://host:3080`; do not append `/v2`. |
| `GNS3_USERNAME` / `GNS3_PASSWORD` | yes | HTTP Basic Auth credentials used by GNS3 2.2. |
| `GNS3_API_VERSION` | no | Must be `v2`; v2 also forces read-only mode. |
| `GNS3_READ_ONLY` | no | Keep `true`; v2 forces it to `true` even if misconfigured. |
| `GNS3_VERIFY_TLS` | no | TLS certificate verification; defaults to `true`. |
| `GNS3_DEFAULT_PROJECT` | no | Project UUID used when a tool omits `project_id`. |
| `GNS3_CONSOLE_TIMEOUT` | no | Console read timeout in seconds; defaults to `15`. |

The v2 client does not call `/access/users/login` and does not use bearer-token
authentication. Credentials are supplied to the HTTP client as Basic Auth and
are never returned by MCP tools.

## Install locally

From this repository, use an isolated environment when possible:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
```

For a direct local install, the package provides the `gns3-mcp` command:

```bash
GNS3_API_VERSION=v2 GNS3_READ_ONLY=true \
GNS3_BASE_URL=http://gns3-host:3080 \
GNS3_USERNAME=admin GNS3_PASSWORD='…' \
gns3-mcp
```

## Register in Codex

The repository includes a Claude-compatible plugin manifest at
`plugin/.mcp.json`. For a direct Codex stdio registration, use the installed
command and supply credentials through the environment rather than committing
them to a file:

```bash
codex mcp add gns3-readonly \
  --env GNS3_API_VERSION=v2 \
  --env GNS3_READ_ONLY=true \
  --env GNS3_BASE_URL=http://gns3-host:3080 \
  --env GNS3_USERNAME=admin \
  --env GNS3_PASSWORD='…' \
  -- gns3-mcp
```

Verify registration with `codex mcp list`. The server uses stdio and starts on
demand when Codex invokes it; it does not need a permanently running daemon.

## Safety boundary

The v2 configuration forces `read_only=true`. Mutating tool modules are not
registered, and diagnostic console commands are validated against a strict
allowlist. This is a read-only inspection bridge, not a mechanism for changing
the lab.

## Development and verification

```bash
python -m pytest -q
```

The tests cover v2 Basic Auth, forced read-only settings, the reduced tool
profile, and command validation. A live controller smoke test should be run
only with a real v2 controller and must use non-destructive GET/diagnostic
operations.
