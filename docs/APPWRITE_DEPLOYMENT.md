# Deployment: Docker + Appwrite

## Local library and tests (unchanged)

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest -q
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
- **`src/mcore_py/`** and **`src/mcore_1/`** (copy into the artifact root, or install from a Git tarball in `commands`)

Recommended CI job (outline):

1. `rsync -a src/mcore_py src/mcore_1 functions/check_tree/bundle/src/`
2. `cd functions/check_tree/bundle && zip -r ../deploy.zip .`
3. `appwrite functions create-deployment --function-id ... --code deploy.zip` (see current CLI flags in your CLI version)

Alternatively, publish **`mcore-py`** to a private package index and `pip install mcore-py==...` in the function `commands` step.

## Multi-stage Docker (optional gateway)

If you run **mcore-mcp** as a sidecar HTTP service in Kubernetes:

```dockerfile
FROM python:3.12-slim AS base
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir -e ".[appwrite]"
COPY src/mcore_mcp ./src/mcore_mcp
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "mcore_mcp.server", "--transport", "http", "--host", "0.0.0.0", "--port", "8765"]
```

> The `mcore_mcp.server` CLI flags follow FastMCP’s `run()` options; adjust to your FastMCP version.

## HANDOFF_TO_GJB2 integration

Paper repos should consume **`mcore_1`** as a library. Appwrite persistence is **orthogonal**: store `NodeResult` JSON from `check_tree` / `check_deletion` in `bisection_tree_runs` / `gjb2_results` for collaboration; keep mathematical semantics identical to `HANDOFF_TO_GJB2.md`.
