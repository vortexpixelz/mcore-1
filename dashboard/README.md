# Symonic Trust Dashboard v0.1

This directory is the first repo-native cockpit for Symonic control-state telemetry.

It turns repo artifacts into machine-readable dashboard data:

```text
CLAIMS.md + receipts/*.md + git metadata + workspace exports
        ↓
dashboard/scripts/build_dashboard_data.py
        ↓
dashboard/data/*.json
        ↓
Grafana panels
```

## Quick start

From the repo root:

```bash
python dashboard/scripts/build_dashboard_data.py
python -m http.server 8088 --directory dashboard/data
```

Then in Grafana:

1. Install either the **Infinity** or **JSON API** data source plugin.
2. Add a data source pointed at `http://localhost:8088`.
3. Import `dashboard/grafana/symonic-trust-dashboard.json`.

## Data files

- `dashboard/data/trust_state.json` is generated from the repo.
- `dashboard/data/funding.json` is hand-maintained for now.
- `dashboard/data/workspace.json` is hand-maintained from Google Workspace exports/screenshots until API wiring exists.

## v0.1 Panels

- Claim tier counts
- Receipt freshness
- Repo integrity checks
- Funding pipeline state
- Workspace account/security state

## Design rule

Grafana is only the window. The canonical system state lives in versioned JSON files so the dashboard can be audited, committed, reviewed, and eventually fed by Appwrite/MCP.
