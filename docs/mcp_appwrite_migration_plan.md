# FastMCP-First Architecture & Appwrite Deprecation Path

> **Status:** Draft — created as part of scoping task  
> **Scope:** `mcore-1` repository  
> **Goal:** Establish FastMCP as the primary local/dev/research interface; reduce Appwrite to an optional adapter or removable layer.

---

## 1. Current State

### 1.1 FastMCP surfaces (`src/mcore_mcp/`)

| File | Role |
|------|------|
| `server.py` | 14 MCP tools exposed via FastMCP; handles metrical algebra, DNA encoding, bisection trees, methylation/quantum overlays, acoustic synthesis, Base64-TME, and one direct Appwrite executor tool (`mcore_appwrite_exec_check_tree`) |
| `delegate.py` | Thin gate: if `APPWRITE_USE_FUNCTIONS=true` and all `APPWRITE_*` env vars are set, routes `check_tree_weights`, `check_tree_dna`, and `check_deletion` to the remote Function instead of running them locally |
| `analytics.py` | Optional PostHog client (no-ops when `POSTHOG_API_KEY` is absent) |
| `overlay_tools.py` | Pure computation helpers (methylation, quantum, acoustic, TME) — zero cloud dependency |

All 13 core tools work **with zero Appwrite config** today; the delegation and `mcore_appwrite_exec_check_tree` tool are the only Appwrite-coupled paths.

### 1.2 Appwrite SDK layer (`src/mcore_appwrite/`)

| File | Role |
|------|------|
| `config.py` | Reads `APPWRITE_ENDPOINT`, `APPWRITE_PROJECT_ID`, `APPWRITE_API_KEY`, `APPWRITE_FUNCTION_CHECK_TREE_ID`, `APPWRITE_USE_FUNCTIONS` |
| `client.py` | Builds Appwrite admin SDK `Client` (server key, never browser) |
| `executor.py` | `execute_check_tree_function`: fires `Functions.create_execution` with POST + JSON body, polls `get_execution` until `responseBody` is populated |

### 1.3 Appwrite Functions (`functions/`)

| Path | Role |
|------|------|
| `functions/check_tree/src/main.py` | Appwrite Function runtime: handles `dna_encode`, `check_tree_weights`, `check_tree_dna`, `check_deletion` ops; vendors `mcore_1`/`mcore_py` into `mcore_src/` |
| `functions/check_tree/mcore_src/` | Vendored copy of `src/mcore_1` and `src/mcore_py` (must be kept in sync manually) |
| `functions/mcore-mcp/main.py` | Appwrite Function gateway: translates MCP-shaped or passthrough JSON and forwards to `check_tree` via another `Functions.create_execution` call |
| `functions/*/requirements.txt` | `appwrite>=6.0`, optional `numpy`, `posthog` |

### 1.4 Docker (`Dockerfile`)

Installs `.[dev,analysis]` — **does not install the `mcp` extra**. FastMCP, `appwrite` SDK, and `posthog` are absent from the container image. Default `CMD` runs pytest. No Appwrite interaction in the Docker layer.

### 1.5 CI (`.github/workflows/python-app.yml`)

Two jobs:
- **build**: `uv sync --extra dev --extra analysis --extra mcp` → ruff → pytest (includes `appwrite>=6.1` and `fastmcp>=2.3`)
- **docker**: builds image (no `mcp` extra) and runs pytest inside container

No Appwrite credentials in CI; no smoke tests against a live Appwrite instance.

### 1.6 Appwrite-specific documentation (`docs/`)

`APPWRITE_ARCHITECTURE.md`, `APPWRITE_DATABASE_SCHEMA.md`, `APPWRITE_DEPLOYMENT.md`, `APPWRITE_FUNCTIONS_EXAMPLES.md`, `APPWRITE_QUICKSTART.md`, `APPWRITE_SETUP.md`, `MIGRATION_APPWRITE.md` — six documents describing a cloud integration path that is opt-in and currently untested in CI.

---

## 2. Responsibility Map

### What FastMCP serves (primary path today)

- All 13 core MCP tools (metrical algebra, DNA, bisection, overlays, acoustic) — run fully in-process, no network
- Optional delegation of three `check_tree`-family tools to Appwrite Function (behind env gate)
- One passthrough tool (`mcore_appwrite_exec_check_tree`) that calls the remote Function directly
- Optional PostHog telemetry

### What Appwrite serves (secondary / opt-in path today)

- **Remote compute offload**: executes `check_tree`/`check_deletion`/`dna_encode` in the cloud when `APPWRITE_USE_FUNCTIONS=true`
- **Persistence layer (planned, not yet wired)**: TablesDB schema for patterns, trees, GJB2 results, acoustic metadata — described in docs but no insertion code exists in `src/`
- **Gateway function** (`mcore-mcp`): a second-hop HTTP bridge to `check_tree` (used from within Appwrite Console or external HTTP clients, not from the Python MCP server)
- **Auth, Realtime, Storage, Messaging** (described in architecture docs, not yet implemented in this repo)

### What is duplicated

| Logic | FastMCP path | Appwrite path |
|-------|-------------|---------------|
| `check_tree_weights` | `mcore_1.check_tree.check_tree` | `functions/check_tree/src/main.py` op `check_tree_weights` |
| `check_tree_dna` | `mcore_1.encoder.dna_to_trits` + `check_tree` | Same ops in function |
| `check_deletion` | `mcore_1.check_tree.check_deletion` | `functions/check_tree/src/main.py` op `check_deletion` |
| Execution polling loop | `src/mcore_appwrite/executor.py` | `functions/mcore-mcp/main.py` |
| `mcore_1`/`mcore_py` library | `src/` (canonical) | `functions/check_tree/mcore_src/` (vendored copy) |

### What is only needed for Appwrite deployment

- `functions/check_tree/` — Appwrite Function bundle
- `functions/mcore-mcp/` — Appwrite gateway bundle
- `functions/check_tree/mcore_src/` — vendored library copy
- `appwrite/`, `appwrite.config.example.json` — deployment config
- `src/mcore_appwrite/` — Python SDK wrapper
- `src/mcore_mcp/delegate.py` — delegation gate
- `mcore_appwrite_exec_check_tree` tool in `server.py`
- `docs/APPWRITE_*.md`, `docs/MIGRATION_APPWRITE.md`
- `appwrite` and `posthog` entries in `pyproject.toml` `[mcp]` extra
- `APPWRITE_*` entries in `.env.example`

---

## 3. Proposed Target Architecture

### Principle: FastMCP-first, Appwrite as optional adapter

```
┌─────────────────────────────────────────────────────────────┐
│  Local / dev / research (default)                           │
│                                                             │
│  uv run python -m mcore_mcp.server                         │
│       └── FastMCP (stdio or HTTP)                           │
│             ├── mcore_py  (algebra, overlays, audio, TME)   │
│             └── mcore_1   (DNA, bisection, check_tree)      │
└─────────────────────────────────────────────────────────────┘
             │  optional adapter (env-gated, disabled by default)
             ▼
┌─────────────────────────────────────────────────────────────┐
│  Appwrite adapter (future optional extra or separate pkg)   │
│                                                             │
│  - Persistence: TablesDB rows (patterns, trees, GJB2)       │
│  - Auth: user sessions, row-level security                  │
│  - Remote compute: Functions as scaling option only         │
└─────────────────────────────────────────────────────────────┘
```

### 3.1 FastMCP primary (keep, strengthen)

- `src/mcore_mcp/server.py` — core of all MCP tooling; keep all 13 core tools
- `src/mcore_mcp/overlay_tools.py` — pure helpers; keep as-is
- `src/mcore_mcp/analytics.py` — keep; PostHog is optional and already no-ops without key
- `src/mcore_py/`, `src/mcore_1/` — canonical library; no changes needed

### 3.2 Appwrite as optional adapter (isolate, gate behind install extra)

- Move Appwrite-coupled code to a distinct `appwrite` optional extra (`pip install mcore-py[appwrite]`) — currently it is bundled in `[mcp]`, adding a compile-time `appwrite>=6.1` dependency to all MCP users
- `src/mcore_appwrite/` stays but is only imported when `[appwrite]` extra is installed
- `src/mcore_mcp/delegate.py` — keep, but guard import with `importlib` or `TYPE_CHECKING` so the MCP server starts without `appwrite` installed
- `mcore_appwrite_exec_check_tree` tool in `server.py` — keep for now but add a runtime guard (currently it already imports lazily on call)

### 3.3 uv-native local dev (strengthen)

- `Dockerfile` should gain a `mcp` install stage or separate target so the MCP server can be run in Docker without Appwrite credentials
- CI should add a smoke-test of the MCP server under stdio transport (no Appwrite)
- `mcp/README.md` is already good; update to emphasise zero-dependency default path

### 3.4 Appwrite optional path (do not delete yet — deprecation markers only)

- Add `# DEPRECATED: ...` header comments to `functions/check_tree/` and `functions/mcore-mcp/` noting they are Appwrite-only and not exercised by CI
- Add deprecation notice to all `docs/APPWRITE_*.md` pointing at this document
- Document that `mcore_src/` in `functions/check_tree/` must be kept in sync with `src/` until the function is removed

---

## 4. Files to Keep

| Path | Reason |
|------|--------|
| `src/mcore_py/` | Core library — canonical and stable |
| `src/mcore_1/` | DNA, bisection, GJB2 — canonical |
| `src/mcore_mcp/server.py` | FastMCP server — primary interface |
| `src/mcore_mcp/overlay_tools.py` | Pure helpers |
| `src/mcore_mcp/analytics.py` | Optional PostHog — no-ops cleanly |
| `src/mcore_mcp/__init__.py` | Package init |
| `mcp/README.md` | Developer entry point |
| `Dockerfile` | CI / reproducible env (needs mcp-stage addition) |
| `.github/workflows/python-app.yml` | CI |
| `pyproject.toml` | Build config |
| `.env.example` | Env reference (trim Appwrite section or mark optional) |

---

## 5. Files to Deprecate (Do Not Delete Yet)

| Path | Deprecation rationale |
|------|----------------------|
| `src/mcore_appwrite/config.py` | Appwrite-only; should become part of optional extra |
| `src/mcore_appwrite/client.py` | Appwrite SDK dependency |
| `src/mcore_appwrite/executor.py` | Execution polling; duplicated in `functions/mcore-mcp/` |
| `src/mcore_mcp/delegate.py` | Only needed if Appwrite Functions delegation is active |
| `mcore_appwrite_exec_check_tree` (in `server.py`) | Direct Appwrite tool; not part of core MCP surface |
| `functions/check_tree/` | Appwrite Function bundle; not tested in CI |
| `functions/mcore-mcp/` | Appwrite gateway Function; not tested in CI |
| `functions/check_tree/mcore_src/` | Vendored library copy; divergence risk |
| `appwrite/` | Appwrite Console config |
| `appwrite.config.example.json` | Appwrite project config example |
| `docs/APPWRITE_ARCHITECTURE.md` | Describes planned Appwrite-first vision |
| `docs/APPWRITE_DATABASE_SCHEMA.md` | TablesDB schema (no insertion code exists) |
| `docs/APPWRITE_DEPLOYMENT.md` | Deployment runbook for Appwrite Functions |
| `docs/APPWRITE_FUNCTIONS_EXAMPLES.md` | Function usage examples |
| `docs/APPWRITE_QUICKSTART.md` | Quickstart for Appwrite path |
| `docs/APPWRITE_SETUP.md` | Setup guide for Appwrite project |
| `docs/MIGRATION_APPWRITE.md` | Describes migrating data *to* Appwrite (opposite direction) |
| `appwrite` and `posthog` in `[mcp]` extra (pyproject.toml) | Should move to `[appwrite]` extra |

---

## 6. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| `appwrite>=6.1` is bundled in `[mcp]` — all MCP users pull in the full SDK even without Appwrite | Medium | Split into `[appwrite]` extra; update CI to test without it |
| `functions/check_tree/mcore_src/` drifts from canonical `src/` | High | Already out-of-scope for CI; add a lint/hash check or remove in the deprecation PR |
| Lazy imports in `server.py` (`from mcore_appwrite...` inside function body) could raise `ImportError` at call time if user installed `[mcp]` only (after the split) | Medium | Add explicit `importlib.util.find_spec("appwrite")` guard and return `{"error": "appwrite extra not installed"}` instead of raising |
| Docs reference Appwrite as the intended persistence/auth layer — removing them without a replacement narrative would leave a gap | Low | This document serves as the bridge; add a "local-first persistence" section in a follow-up |
| `posthog` in `[mcp]` extra — same bundling concern as `appwrite` | Low | Move to `[appwrite]` or keep in `[mcp]` since it already no-ops without a key |

---

## 7. Migration Steps

### Phase 1 — Isolate (recommended next PR)

1. Add `appwrite` optional extra to `pyproject.toml`, separate from `[mcp]`:
   ```toml
   [project.optional-dependencies]
   appwrite = ["appwrite>=6.1"]
   mcp = ["fastmcp>=2.3", "posthog>=3.7", "numpy>=1.24"]
   ```
2. In `src/mcore_mcp/delegate.py`, guard the `mcore_appwrite` import with `importlib.util.find_spec`:
   ```python
   def delegate_check_tree(op, payload):
       if importlib.util.find_spec("appwrite") is None:
           return None
       ...
   ```
3. In `server.py`, update `mcore_appwrite_exec_check_tree` to return `{"error": "appwrite extra not installed"}` when the `appwrite` package is absent, rather than raising `ImportError`.
4. Update CI: add a job `test-no-appwrite` that runs `uv sync --extra dev --extra mcp` (without `[appwrite]`) and verifies the server imports and all non-Appwrite tools pass.
5. Update `Dockerfile` to install `.[dev,analysis,mcp]` so the container can run the MCP server.

### Phase 2 — Mark deprecated

6. Add `# DEPRECATED — Appwrite Function; not required for FastMCP-first path` header comments in `functions/check_tree/src/main.py` and `functions/mcore-mcp/main.py`.
7. Add a deprecation notice block to all `docs/APPWRITE_*.md` and `docs/MIGRATION_APPWRITE.md` pointing at this document.
8. Update `mcp/README.md` to prominently document the zero-Appwrite default.

### Phase 3 — Clean up (future PR, after Phase 1 validates)

9. Delete `functions/check_tree/`, `functions/mcore-mcp/`, `appwrite/`, `appwrite.config.example.json`, `docs/APPWRITE_*.md`, `docs/MIGRATION_APPWRITE.md`.
10. Delete `src/mcore_appwrite/` and `src/mcore_mcp/delegate.py`.
11. Remove `mcore_appwrite_exec_check_tree` tool from `server.py`.
12. Remove `APPWRITE_*` vars from `.env.example`.

---

## 8. Tests Required

| Test | Phase | Description |
|------|-------|-------------|
| `test_mcp_no_appwrite` | 1 | Import `mcore_mcp.server` without `appwrite` installed; assert all 13 core tools are registered and callable |
| `test_delegate_no_appwrite` | 1 | `delegate_check_tree(...)` returns `None` when `appwrite` is not installed |
| `test_appwrite_tool_guard` | 1 | `mcore_appwrite_exec_check_tree` returns `{"error": ...}` dict (not raises) when `appwrite` absent |
| `test_mcp_smoke_docker` | 1 | Docker `CMD` can run `python -m mcore_mcp.server --help` without error |
| `test_delegate_with_appwrite` | 2 | Existing mock-based delegate test remains green after refactor |
| `test_functions_check_tree_unit` | existing | `functions/check_tree/src/main.py` unit-testable locally without Appwrite runtime |

Existing tests: `tests/test_mcp_smoke.py`, `tests/test_mcp_overlay_smoke.py`, `tests/test_analytics_optional.py` — these should all remain green throughout.

---

## 9. Recommended Next PR

**PR title:** `feat: isolate appwrite into optional extra; FastMCP server starts without cloud deps`

**Scope (Phase 1 above):**

1. Add `[appwrite]` extra to `pyproject.toml`; remove `appwrite>=6.1` from `[mcp]`
2. Add `importlib.util.find_spec("appwrite")` guard in `delegate.py`
3. Add soft `ImportError` guard in `mcore_appwrite_exec_check_tree` (already lazy-imports; add a `find_spec` check before the `from` statement)
4. Add `test-no-appwrite` CI job
5. Update `Dockerfile` to include `mcp` extra
6. Update `mcp/README.md` — zero-cloud default section

This PR is low-risk (no deletions, no logic changes to core tools), directly improves the developer experience for all users who do not use Appwrite, and unblocks Phase 2 cleanup.
