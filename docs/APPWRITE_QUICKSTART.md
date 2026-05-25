# Appwrite + MCP quickstart (one screen)

## The one-liners

- **Local MCP (Inspector):**  
  `uv sync --extra dev --extra mcp --extra analysis && ./scripts/mcp_dev.sh`

- **Bundle the `check_tree` Function:**  
  `./scripts/package_check_tree_bundle.sh`

- **Deploy Function (after `appwrite login`, with `APPWRITE_FUNCTION_ID` set):**  
  `export APPWRITE_FUNCTION_ID=mcore_check_tree && ./scripts/deploy_appwrite_function.sh`

- **Smoke-test a deployed function (replace host + project + id):**  
  `curl -sS -X POST "https://<REGION>.cloud.appwrite.io/v1/functions/<FUNCTION_ID>/executions" -H "X-Appwrite-Project: <PROJECT>" -H "X-Appwrite-Key: <API_KEY>" -H "Content-Type: application/json" -d '{"data":{"op":"dna_encode","dna":"ACGT"}}'`

  (Exact REST path may differ slightly by Appwrite version — prefer **Console → Functions → Execute** for first validation.)

## 1. Local math + tests (no cloud)

```bash
uv sync --extra dev --extra analysis
uv run pytest -q
```

## 2. Live MCP (Inspector) — same as `uv sync && mcp dev`

From the repository root (requires `uv` and `fastmcp` on PATH after sync):

```bash
uv sync --extra dev --extra mcp --extra analysis && ./scripts/mcp_dev.sh
```

Equivalent manual command:

```bash
uv sync --extra dev --extra mcp --extra analysis
uv run fastmcp dev inspector -m mcore_mcp.server
```

This opens the **MCP Inspector** UI (FastMCP `dev inspector`) against the `MCORE-1` server.

**List tools (CI-friendly, no browser):**

```bash
uv sync --extra mcp --quiet
PYTHONPATH=src uv run fastmcp list src/mcore_mcp/server.py --json
```

## 3. Bundle + deploy the `check_tree` Function

Prerequisites: `appwrite login`, `appwrite init project`, function `$id` created in Console matching `APPWRITE_FUNCTION_ID`.

**Build command in Console:** `pip install -r requirements.txt` (see `functions/check_tree/README.md`).

```bash
export APPWRITE_FUNCTION_ID="mcore_check_tree"   # your function $id
./scripts/package_check_tree_bundle.sh
./scripts/deploy_appwrite_function.sh
```

If your CLI version does not upload the zip from `push` alone, create a deployment in the Console using `.build/check_tree_deploy.zip` produced by the package script.

## 4. Point MCP at remote `check_tree`

```bash
export APPWRITE_ENDPOINT="https://<REGION>.cloud.appwrite.io/v1"
export APPWRITE_PROJECT_ID="…"
export APPWRITE_API_KEY="…"
export APPWRITE_FUNCTION_CHECK_TREE_ID="mcore_check_tree"
export APPWRITE_USE_FUNCTIONS=true
./scripts/mcp_dev.sh
```

## 5. PostHog (optional)

```bash
export POSTHOG_API_KEY="phc_…"
export POSTHOG_HOST="https://us.i.posthog.com"
```

See `.env.example` for the full list.
