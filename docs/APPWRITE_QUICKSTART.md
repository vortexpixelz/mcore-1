# Appwrite + MCP quickstart (one screen)

## The one-liners

- **Local MCP (Inspector):**  
  `uv sync --extra dev --extra mcp --extra analysis && ./scripts/mcp_dev.sh`

- **Bundle + vendor for Git deploy:**  
  `./scripts/package_check_tree_bundle.sh`  
  then **commit + push** `functions/check_tree/mcore_src/` so Appwrite Git builds include `mcore_py` / `mcore_1`.

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

**Deployment directory:** must be **`functions/check_tree`** (Git path in this repo — **not** `functions/mcore_check_tree`; the function *id* can still be `mcore_check_tree`). If pip cannot open `requirements.txt`, the root path or branch is wrong.

```bash
export APPWRITE_FUNCTION_ID="mcore_check_tree"   # your function $id
./scripts/package_check_tree_bundle.sh
./scripts/deploy_appwrite_function.sh
```

If your CLI version does not upload the zip from `push` alone, create a deployment in the Console using `.build/check_tree_deploy.zip` produced by the package script.

## 3b. Optional: MCP gateway Function (`mcore-mcp`)

Second Appwrite function that **forwards** JSON to `mcore_check_tree` (Path A — HTTP tool bridge, not full FastMCP). See **`functions/mcore-mcp/README.md`**.

- **Deployment directory:** **`functions/mcore-mcp`** (must match Git; hyphen in `mcore-mcp`, not `mcore_mcp`)
- **Build command:** `pip install -r requirements.txt`
- **Entrypoint:** `main.py`

If pip errors with **`No such file or directory: 'requirements.txt'`**, the deployment root is wrong or the branch does not contain `functions/mcore-mcp/`. Fix the root path, or use `pip install -r functions/mcore-mcp/requirements.txt` and entrypoint `functions/mcore-mcp/main.py` when the build must run from **repo root**.

Set the same `APPWRITE_*` variables on this function, plus **`APPWRITE_FUNCTION_CHECK_TREE_ID`** pointing at your check_tree function’s `$id`. When the gateway runs **as** an Appwrite Function, prefer the injected **`x-appwrite-key`** and **`APPWRITE_FUNCTION_PROJECT_ID`** (see `functions/mcore-mcp/README.md`); grant **Scopes** to create executions on the target function.

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
