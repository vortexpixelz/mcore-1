#!/usr/bin/env bash
# Vendors mcore_py + mcore_1 for Appwrite Git deploys, and builds a zip for manual upload.
#
# Usage:
#   package_check_tree_bundle.sh [OUT_ZIP]  Vendor into functions/check_tree/mcore_src, build zip.
#   package_check_tree_bundle.sh --check    Verify the committed vendored copy still matches
#                                           src/. Read-only; exits non-zero on drift.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

DEST="$ROOT/functions/check_tree/mcore_src"

# Drift guard: the vendored tree is a plain copy of src/, so any divergence means a change
# landed in one and not the other. Vendor into a scratch dir and compare; never touch the
# working tree. __pycache__/*.pyc are gitignored and are not part of the vendored contract.
if [[ "${1:-}" == "--check" ]]; then
    TMP="$(mktemp -d)"
    trap 'rm -rf "$TMP"' EXIT
    cp -a "$ROOT/src/mcore_py" "$ROOT/src/mcore_1" "$TMP/"
    if diff -r -x '__pycache__' -x '*.pyc' "$TMP" "$DEST"; then
        echo "OK: functions/check_tree/mcore_src is in sync with src/"
        exit 0
    fi
    echo "" >&2
    echo "ERROR: functions/check_tree/mcore_src has drifted from src/." >&2
    echo "Above, '<' is src/ (expected) and '>' is the vendored copy (committed)." >&2
    echo "Regenerate and commit with: scripts/package_check_tree_bundle.sh" >&2
    exit 1
fi

OUT="${1:-${ROOT}/.build/check_tree_deploy.zip}"
mkdir -p "$(dirname "$OUT")"

rm -rf "$DEST"
mkdir -p "$DEST"
cp -a "$ROOT/src/mcore_py" "$ROOT/src/mcore_1" "$DEST/"
echo "Vendored src/mcore_py and src/mcore_1 → functions/check_tree/mcore_src/"

( cd "$ROOT/functions/check_tree" && zip -r -q "$OUT" . \
    -x 'mcore_src/**/__pycache__/*' -x 'mcore_src/**/*.pyc' -x 'src/__pycache__/*' -x 'src/**/*.pyc' )
echo "Wrote $OUT"
