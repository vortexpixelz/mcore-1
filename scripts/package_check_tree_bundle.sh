#!/usr/bin/env bash
# Vendors mcore_py + mcore_1 for Appwrite Git deploys, and builds a zip for manual upload.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-${ROOT}/.build/check_tree_deploy.zip}"
mkdir -p "$(dirname "$OUT")"

DEST="$ROOT/functions/check_tree/mcore_src"
rm -rf "$DEST"
mkdir -p "$DEST"
cp -a "$ROOT/src/mcore_py" "$ROOT/src/mcore_1" "$DEST/"
echo "Vendored src/mcore_py and src/mcore_1 → functions/check_tree/mcore_src/"

( cd "$ROOT/functions/check_tree" && zip -r -q "$OUT" . \
    -x 'mcore_src/**/__pycache__/*' -x 'mcore_src/**/*.pyc' -x 'src/__pycache__/*' -x 'src/**/*.pyc' )
echo "Wrote $OUT"
