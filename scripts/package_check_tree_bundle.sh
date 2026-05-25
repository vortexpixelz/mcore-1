#!/usr/bin/env bash
# Build a deployable zip for Appwrite Function mcore_check_tree (see functions/check_tree/README.md).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-${ROOT}/.build/check_tree_deploy.zip}"
mkdir -p "$(dirname "$OUT")"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/mcore_src"
cp -a "$ROOT/functions/check_tree/src" "$TMP/"
cp -a "$ROOT/functions/check_tree/requirements.txt" "$TMP/"
cp -a "$ROOT/src/mcore_py" "$ROOT/src/mcore_1" "$TMP/mcore_src/"
( cd "$TMP" && zip -r -q "$OUT" . )
echo "Wrote $OUT"
