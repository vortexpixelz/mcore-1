#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

python dashboard/scripts/build_dashboard_data.py
python -m http.server 8088 --directory dashboard/data
