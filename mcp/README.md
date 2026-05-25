# MCP (Model Context Protocol)

Implementation: **`src/mcore_mcp/`** (`mcore_mcp` package). Prefer **uv**:

```bash
uv sync --extra dev --extra mcp --extra analysis
uv run python -m mcore_mcp.server
```

Or classic pip:

```bash
python3 -m pip install -e ".[mcp]"
python3 -m mcore_mcp.server
```

## Tools (overview)

| Prefix | Area |
|--------|------|
| `mcore_validate_*`, `mcore_complete_*`, `mcore_trit_*`, `mcore_pattern_*` | Core algebra + TME |
| `mcore_dna_*`, `mcore_check_tree_*`, `mcore_check_deletion` | `mcore_1` / GJB2 |
| `mcore_methylation_*`, `mcore_quantum_*` | Overlays + trajectories |
| `mcore_acoustic_*` | Gaussian phonon synthesis / FFT roundtrip |
| `mcore_appwrite_*` | Raw Appwrite Function execution |

Full list: `PYTHONPATH=src uv run fastmcp list src/mcore_mcp/server.py --json`

## MCP Inspector (dev UI)

```bash
./scripts/mcp_dev.sh
```

Equivalent: `uv sync --extra dev --extra mcp --extra analysis && uv run fastmcp dev inspector -m mcore_mcp.server`

## Claude Desktop (example)

```json
{
  "mcpServers": {
    "mcore-1": {
      "command": "uv",
      "args": ["run", "python", "-m", "mcore_mcp.server"],
      "cwd": "/absolute/path/to/mcore-1"
    }
  }
}
```

## Appwrite delegation

See root **`.env.example`**: `APPWRITE_*`, `APPWRITE_USE_FUNCTIONS=true` to route heavy `check_tree` tools through the Function.

## Appwrite MCP-for-API

Use `appwrite generate` for typed TablesDB clients; this MCP stays **domain-first**.
