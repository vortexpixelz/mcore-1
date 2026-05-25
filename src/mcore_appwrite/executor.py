"""Execute the bundled ``mcore_check_tree`` Appwrite Function."""

from __future__ import annotations

import json
import time
from typing import Any

from mcore_appwrite.client import build_admin_client
from mcore_appwrite.config import AppwriteConfig


def _execution_response(execution: Any) -> tuple[Any, Any]:
    if isinstance(execution, dict):
        return execution.get("responseBody"), execution.get("responseStatusCode")
    rb = (
        getattr(execution, "response_body", None)
        or getattr(execution, "responseBody", None)
        or getattr(execution, "responsebody", None)
    )
    sc = (
        getattr(execution, "response_status_code", None)
        or getattr(execution, "responseStatusCode", None)
        or getattr(execution, "responsestatuscode", None)
        or 200
    )
    if rb is None and hasattr(execution, "model_dump"):
        dump = execution.model_dump(by_alias=True)
        rb = dump.get("responseBody")
        sc = dump.get("responseStatusCode", sc)
    return rb, sc


def _execution_id(execution: Any) -> str | None:
    if isinstance(execution, dict):
        x = execution.get("$id") or execution.get("id")
        return str(x) if x else None
    if hasattr(execution, "model_dump"):
        d = execution.model_dump(by_alias=True)
        x = d.get("$id") or d.get("id")
        if x:
            return str(x)
    for name in ("$id", "id"):
        v = getattr(execution, name, None)
        if v:
            return str(v)
    return None


def _execution_status(execution: Any) -> str:
    if isinstance(execution, dict):
        return str(execution.get("status") or "").lower()
    st = getattr(execution, "status", None)
    if st is None and hasattr(execution, "model_dump"):
        st = execution.model_dump(by_alias=True).get("status")
    return str(st or "").lower()


def execute_check_tree_function(cfg: AppwriteConfig, payload: dict[str, Any]) -> dict[str, Any]:
    """Run the remote function and parse JSON from ``responseBody``."""
    if not cfg.check_tree_function_id:
        raise RuntimeError("APPWRITE_FUNCTION_CHECK_TREE_ID is not set")

    from appwrite.enums.execution_method import ExecutionMethod
    from appwrite.services.functions import Functions

    client = build_admin_client(cfg)
    functions = Functions(client)
    fid = cfg.check_tree_function_id
    execution = functions.create_execution(
        function_id=fid,
        body=json.dumps(payload),
        xasync=False,
        method=ExecutionMethod.POST,
    )
    ex_id = _execution_id(execution)
    for i in range(60):
        raw, status = _execution_response(execution)
        st = _execution_status(execution)
        has_body = (isinstance(raw, str) and raw.strip()) or (isinstance(raw, dict) and bool(raw))
        if has_body:
            break
        if st in ("failed", "canceled", "cancelled"):
            break
        if st == "completed" and i >= 2:
            break
        if not ex_id:
            break
        time.sleep(0.2)
        execution = functions.get_execution(function_id=fid, execution_id=ex_id)

    raw, status = _execution_response(execution)
    if raw in (None, "") or (isinstance(raw, str) and not raw.strip()):
        return {"_execution": execution, "error": "empty_response_body"}
    if isinstance(raw, dict):
        out = raw
    else:
        try:
            out = json.loads(raw)
        except json.JSONDecodeError as e:
            return {"error": "invalid_json", "detail": str(e), "raw": str(raw)[:500]}
    if isinstance(status, int) and status >= 400:
        return {"error": "function_http_error", "status": status, "body": out}
    return out
