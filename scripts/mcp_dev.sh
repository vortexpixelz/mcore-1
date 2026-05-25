#!/usr/bin/env bash
# Local MCP Inspector: same as documented README one-liner (uv + fastmcp).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if command -v uv >/dev/null 2>&1; then
  uv sync --extra dev --extra mcp --extra analysis --quiet
  exec uv run fastmcp dev inspector -m mcore_mcp.server "$@"
else
  echo "uv not found; using current Python env" >&2
  exec fastmcp dev inspector -m mcore_mcp.server "$@"
fi
