# Appwrite Function: `mcore_check_tree`

Serverless entry that mirrors the stable **`mcore_1.check_tree`** API and DNA carry encoding (`dna_to_trits`). Intended for high-throughput clients; the MCP server can delegate here when `APPWRITE_FUNCTION_CHECK_TREE_ID` is set.

## Appwrite Console: Build command (required)

In **Functions → your function → Settings → Build command**, set **exactly**:

```text
pip install -r requirements.txt
```

Do **not** leave `pip install` with no arguments — Appwrite runs that literally and pip errors with: *You must give at least one requirement to install*.

### Deployment directory (critical)

The build **must** run with **`functions/check_tree/`** as the deployment root (Appwrite: **Deployment directory** = `functions/check_tree`, not `/` and not repo root).

If the build log shows **`torch==`**, **`jupyter`**, **`scipy==1.17.1`**, etc., Appwrite is reading the **repo root** `requirements.txt` (the analysis stack). That file is **not** for this function and **torch has no wheel** on many Open Runtimes / Python builds — the install will fail.

**Correct:** only `functions/check_tree/requirements.txt` is used (small set: `numpy`, `appwrite`, `posthog`).

**Workaround if you must deploy from repo root:** set the build command to  
`pip install -r functions/check_tree/requirements.txt`  
and ensure **Entrypoint** still points at the handler under `functions/check_tree/` (e.g. `functions/check_tree/src/main.py` from repo root — depends on Appwrite version; prefer **narrow deployment directory** instead).

After changing it, create a **new deployment** (Git or manual zip).

## Automated bundle (repo root)

From the repository root:

```bash
./scripts/package_check_tree_bundle.sh
```

This writes **`.build/check_tree_deploy.zip`**, which you upload as a new
Function deployment (Console or `appwrite` CLI, depending on version).

## Build layout (critical)

Appwrite deployment archives **only this folder** by default. The Python handler imports `mcore_1` and `mcore_py`, so you must vendor sources **into the deployment bundle**:

```text
functions/check_tree/
  src/main.py
  requirements.txt
  mcore_src/
    mcore_py/     # copy from repo src/mcore_py
    mcore_1/      # copy from repo src/mcore_1
```

The handler prepends `mcore_src` to `sys.path` when present (see `src/main.py`).

### Example packaging script (run from repo root)

```bash
set -euo pipefail
BUNDLE="functions/check_tree/_bundle"
rm -rf "$BUNDLE"
mkdir -p "$BUNDLE/mcore_src"
cp -a functions/check_tree/src "$BUNDLE/"
cp -a functions/check_tree/requirements.txt "$BUNDLE/"
cp -a src/mcore_py src/mcore_1 "$BUNDLE/mcore_src/"
( cd "$BUNDLE" && zip -r ../check_tree_deploy.zip . )
# Upload check_tree_deploy.zip via Console or CLI create-deployment
```

## Request JSON

| `op` | Fields | Response |
|------|--------|----------|
| `dna_encode` | `dna` (string) | `{ "trits": [...], "log": [ ... ] }` |
| `check_tree_weights` | `weights` (list[int]), optional `depth` | `{ "nodes": [ NodeResult, ... ] }` |
| `check_tree_dna` | `dna`, optional `depth` | encodes then same as weights |
| `check_deletion` | `weights_wt`, `weights_mut`, `deletion_pos_1` | `{ "nodes": [...] }` |

Errors return HTTP 400 with `{ "error": "message" }`.

## Environment (optional analytics)

| Variable | Purpose |
|----------|---------|
| `POSTHOG_API_KEY` | Server-side capture for `appwrite_function_check_tree` |
| `POSTHOG_HOST` | Default `https://us.i.posthog.com` |

Call `posthog.shutdown()` before returning (handled in `main.py`).
