"""Execute the bundled ``mcore_check_tree`` Appwrite Function."""

from __future__ import annotations

import json
from typing import Any

from mcore_appwrite.client import build_admin_client
from mcore_appwrite.config import AppwriteConfig


def _execution_response(execution: Any) -> tuple[Any, Any]:
    if isinstance(execution, dict):
        return execution.get("responseBody"), execution.get("responseStatusCode")
    rb = getattr(execution, "responseBody", None)
    sc = getattr(execution, "responseStatusCode", 200)
    return rb, sc


def execute_check_tree_function(cfg: AppwriteConfig, payload: dict[str, Any]) -> dict[str, Any]:
    """Run the remote function and parse JSON from ``responseBody``."""
    if not cfg.check_tree_function_id:
        raise RuntimeError("APPWRITE_FUNCTION_CHECK_TREE_ID is not set")

    from appwrite.services.functions import Functions

    client = build_admin_client(cfg)
    functions = Functions(client)
    execution = functions.create_execution(
        function_id=cfg.check_tree_function_id,
        body=json.dumps(payload),
    )
    raw, status = _execution_response(execution)
    if raw in (None, ""):
        return {"_execution": execution, "error": "empty_response_body"}
    try:
        out = json.loads(raw)
    except json.JSONDecodeError as e:
        return {"error": "invalid_json", "detail": str(e), "raw": raw[:500]}
    if isinstance(status, int) and status >= 400:
        return {"error": "function_http_error", "status": status, "body": out}
    return out
