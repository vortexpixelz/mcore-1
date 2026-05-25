#!/usr/bin/env bash
# One-shot: bundle check_tree + push to Appwrite (requires appwrite CLI + login).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
: "${APPWRITE_FUNCTION_ID:?Set APPWRITE_FUNCTION_ID to your function \$id}"
"$ROOT/scripts/package_check_tree_bundle.sh" "${ROOT}/.build/check_tree_deploy.zip"
appwrite push functions --function-id "$APPWRITE_FUNCTION_ID" --force
echo "Create a new deployment from ${ROOT}/.build/check_tree_deploy.zip if your CLI version requires explicit upload."
