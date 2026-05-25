# Deployment: Docker + Appwrite

## One-command flows

See **[APPWRITE_QUICKSTART.md](./APPWRITE_QUICKSTART.md)** for:

- `uv sync` + MCP Inspector (`./scripts/mcp_dev.sh`)
- Function zip build (`./scripts/package_check_tree_bundle.sh`)
- Push helper (`./scripts/deploy_appwrite_function.sh`)

## Local library and tests (unchanged)

```bash
uv sync --extra dev --extra analysis
uv run pytest -q
```

## Dockerfile (tests / CI)

The root `Dockerfile` continues to target **editable install + pytest**. No Appwrite credentials are required in CI.

## Appwrite Cloud vs self-hosted

| Concern | Appwrite Cloud | Self-hosted |
|---------|----------------|-------------|
| Endpoint | `https://<REGION>.cloud.appwrite.io/v1` | Your TLS URL + `/v1` |
| SSL | Managed | You manage reverse proxy certs |
| Functions build | Remote builders | Your worker capacity |

Set `APPWRITE_ENDPOINT` and `APPWRITE_PROJECT_ID` accordingly.

## Function deployment packaging

Appwrite uploads a **deployment artifact** per function. The `check_tree` function must include:

- `src/main.py` (handler)
- `requirements.txt`
- **`mcore_src/mcore_py/`** and **`mcore_src/mcore_1/`** (see `functions/check_tree/README.md`)

Use **`./scripts/package_check_tree_bundle.sh`** from the repo root to produce `.build/check_tree_deploy.zip`.

Alternatively, publish **`mcore-py`** to a private package index and `pip install mcore-py==...` in the function `commands` step.

## Multi-stage Docker (optional gateway)

If you run **mcore-mcp** as a sidecar HTTP service in Kubernetes:

```dockerfile
FROM python:3.12-slim AS base
WORKDIR /app
COPY pyproject.toml README.md uv.lock ./
COPY src ./src
RUN pip install --no-cache-dir -e ".[mcp]"
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "mcore_mcp.server", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8765"]
```

> Use `streamable-http` per FastMCP; flags may vary slightly by version.

## HANDOFF_TO_GJB2 integration

Paper repos should consume **`mcore_1`** as a library. Appwrite persistence is **orthogonal**: store `NodeResult` JSON from `check_tree` / `check_deletion` in `bisection_tree_runs` / `gjb2_results` for collaboration; keep mathematical semantics identical to `HANDOFF_TO_GJB2.md`.
