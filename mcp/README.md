# MCP (Model Context Protocol)

Implementation package: **`src/mcore_mcp/`** (module `mcore_mcp`). Install extras:

```bash
python3 -m pip install -e ".[mcp]"
```

Run (stdio — Claude Desktop / Cursor):

```bash
python3 -m mcore_mcp.server
```

HTTP (Streamable HTTP):

```bash
python3 -m mcore_mcp.server --transport streamable-http --host 127.0.0.1 --port 8765
```

## Claude Desktop (example)

```json
{
  "mcpServers": {
    "mcore-1": {
      "command": "python3",
      "args": ["-m", "mcore_mcp.server"],
      "cwd": "/absolute/path/to/mcore-1",
      "env": {}
    }
  }
}
```

Add `PYTHONPATH` or use a venv where `mcore-py` is installed editable.

## Appwrite delegation

Set in the environment (see root `.env.example`):

- `APPWRITE_ENDPOINT`, `APPWRITE_PROJECT_ID`, `APPWRITE_API_KEY`
- `APPWRITE_FUNCTION_CHECK_TREE_ID`
- `APPWRITE_USE_FUNCTIONS=true` to route `mcore_check_tree_*` tools through the Function

## Appwrite MCP-for-API

Generate a typed data client with `appwrite generate` and use it beside this server: **this MCP** exposes domain tools; **generated MCP** exposes CRUD aligned with your TablesDB schema.
