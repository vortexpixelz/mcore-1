"""Optional delegation of heavy MCORE ops to Appwrite Functions."""

from __future__ import annotations

from typing import Any

from mcore_appwrite.config import AppwriteConfig, use_remote_check_tree
from mcore_appwrite.executor import execute_check_tree_function


def delegate_check_tree(op: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    """If Appwrite is configured and ``APPWRITE_USE_FUNCTIONS`` is set, run remote function."""
    if not use_remote_check_tree():
        return None
    cfg = AppwriteConfig.from_env()
    if not cfg:
        return None
    body = {"op": op, **payload}
    return execute_check_tree_function(cfg, body)
