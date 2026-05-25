# Appwrite Function: MCP gateway (`mcore_mcp_gateway`)

Thin **HTTP JSON** bridge: forwards payloads to your existing **`mcore_check_tree`** function via the Appwrite server SDK (`Functions.create_execution`). This is **Path A** — not a full FastMCP / stdio MCP server, but enough to call the same ops from another function, a backend, or a custom client without pasting into the check_tree UI.

## Appwrite Console

| Setting | Value |
|--------|--------|
| **Root / deployment directory** | **`functions/mcore-mcp`** |
| **Build command** | `pip install -r requirements.txt` |
| **Entrypoint** | **`main.py`** (handler `main(context)`) |

## Environment variables (function scope)

Same project credentials as other server-side callers, plus the **target** function id:

| Variable | Purpose |
|----------|---------|
| `APPWRITE_ENDPOINT` | e.g. `https://<REGION>.cloud.appwrite.io` (with or without `/v1` — handler normalizes) |
| `APPWRITE_PROJECT_ID` | Project ID |
| `APPWRITE_API_KEY` | API key with permission to **create executions** on `mcore_check_tree` |
| `APPWRITE_FUNCTION_CHECK_TREE_ID` | `$id` of the deployed **check_tree** function (e.g. `mcore_check_tree`) |

## Request shapes (POST JSON)

**1. Tool-style (recommended for a future MCP adapter):**

```json
{
  "tool": "mcore_check_tree",
  "arguments": { "op": "dna_encode", "dna": "ACGT" }
}
```

`tool` may be `mcore_check_tree`, `check_tree`, or `check_tree_function`.

**2. Passthrough** (same body as `functions/check_tree`):

```json
{ "op": "dna_encode", "dna": "ACGT" }
```

## Responses

JSON from **`mcore_check_tree`** is returned as-is (HTTP status mirrored when the execution reports an error). **GET** returns a small health JSON payload.

Logs include a banner and pretty-printed JSON (`=== mcore_mcp_gateway result ===`) before each response.

## Full MCP (Path B)

For native MCP (FastMCP, Inspector, multi-tool), use **`src/mcore_mcp/server.py`** locally or deploy streamable HTTP as documented in that module and `docs/APPWRITE_QUICKSTART.md`.
