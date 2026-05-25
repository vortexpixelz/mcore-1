"""Appwrite Function: JSON gateway → mcore_check_tree (Path A MCP-style bridge).

Not a full MCP protocol server; forwards tool-shaped or passthrough JSON to the
existing check_tree function via Functions.create_execution.
"""

from __future__ import annotations

import json
import os
import time
import traceback
from typing import Any


def _header_get(context, name: str) -> str | None:  # noqa: ANN001
    """Read request header; Open Runtimes use lowercase keys (Appwrite docs)."""
    headers = getattr(context.req, "headers", None)
    if not headers:
        return None
    key = name.lower()
    if isinstance(headers, dict):
        return headers.get(key) or headers.get(name)
    getter = getattr(headers, "get", None)
    if callable(getter):
        v = getter(key)
        return v if v is not None else getter(name)
    return None


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


def _request_method(context) -> str:  # noqa: ANN001
    m = getattr(context.req, "method", None) or "GET"
    return str(m).upper()


def _parse_json_body(context) -> dict[str, Any] | None:  # noqa: ANN001
    """Return a dict payload from body_json, body_text, or Appwrite ``data`` wrapper."""
    raw = getattr(context.req, "body_json", None)
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            raw = None
    if not isinstance(raw, dict):
        text = getattr(context.req, "body_text", None) or getattr(context.req, "bodyText", None)
        if isinstance(text, str) and text.strip():
            try:
                raw = json.loads(text)
            except json.JSONDecodeError:
                raw = None
    if not isinstance(raw, dict):
        return None
    inner = raw.get("data")
    if isinstance(inner, str) and inner.strip():
        try:
            parsed = json.loads(inner)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    elif isinstance(inner, dict):
        return inner
    return raw


def _forward_to_check_tree(context, body: dict[str, Any]) -> dict[str, Any]:  # noqa: ANN001
    """Call check_tree using Appwrite SDK.

    When this handler runs **inside** Appwrite, prefer the per-execution **dynamic
    API key** from ``x-appwrite-key`` and ``APPWRITE_FUNCTION_PROJECT_ID`` (see
    Appwrite Functions docs). Otherwise fall back to ``APPWRITE_API_KEY`` /
    ``APPWRITE_PROJECT_ID`` for local or out-of-band testing.
    """
    fid = os.environ.get("APPWRITE_FUNCTION_CHECK_TREE_ID", "")
    endpoint = (
        os.environ.get("APPWRITE_ENDPOINT", "").rstrip("/")
        or os.environ.get("APPWRITE_FUNCTION_API_ENDPOINT", "").rstrip("/")
    )
    project = (
        os.environ.get("APPWRITE_FUNCTION_PROJECT_ID", "")
        or os.environ.get("APPWRITE_PROJECT_ID", "")
    )
    key = _header_get(context, "x-appwrite-key") or os.environ.get("APPWRITE_API_KEY", "")
    if not (fid and endpoint and project and key):
        return {
            "error": "missing_env",
            "detail": (
                "Need APPWRITE_FUNCTION_CHECK_TREE_ID; API endpoint (APPWRITE_ENDPOINT "
                "or APPWRITE_FUNCTION_API_ENDPOINT); project (APPWRITE_FUNCTION_PROJECT_ID "
                "or APPWRITE_PROJECT_ID); and auth (x-appwrite-key when running as a "
                "Function, else APPWRITE_API_KEY). Grant this function scopes to create "
                "executions on the target function."
            ),
        }

    from appwrite.client import Client
    from appwrite.enums.execution_method import ExecutionMethod
    from appwrite.services.functions import Functions

    ep = endpoint if endpoint.endswith("/v1") else f"{endpoint}/v1"
    client = Client().set_endpoint(ep).set_project(project).set_key(key)
    functions = Functions(client)
    # Child function must see POST + JSON (defaults omitting ``method`` can yield GET).
    execution = functions.create_execution(
        function_id=fid,
        body=json.dumps(body),
        xasync=False,
        method=ExecutionMethod.POST,
    )
    ex_id = _execution_id(execution)
    # Sync create can still return before responseBody is filled — poll get_execution.
    _poll_interval_s = 0.2
    _poll_max = 60
    for i in range(_poll_max):
        raw, status = _execution_response(execution)
        st = _execution_status(execution)
        rb_len = len(raw) if isinstance(raw, str) else (len(json.dumps(raw)) if isinstance(raw, dict) else 0)
        context.log(f"[mcore_mcp] child_exec i={i} id={ex_id!r} status={st!r} rb_type={type(raw).__name__} rb_len={rb_len}")

        has_body = (isinstance(raw, str) and raw.strip()) or (isinstance(raw, dict) and bool(raw))
        if has_body:
            break
        if st in ("failed", "canceled", "cancelled"):
            break
        if st == "completed" and i >= 2:
            break

        if not ex_id:
            break
        time.sleep(_poll_interval_s)
        try:
            execution = functions.get_execution(function_id=fid, execution_id=ex_id)
        except Exception as e:  # noqa: BLE001
            context.log(f"[mcore_mcp] get_execution failed: {e!r}")
            break

    raw, status = _execution_response(execution)
    status_code = int(status) if status is not None else 200
    if raw in (None, "") or (isinstance(raw, str) and not raw.strip()):
        dbg = ""
        if hasattr(execution, "model_dump"):
            try:
                dbg = json.dumps(execution.model_dump(by_alias=True), default=str)[:8000]
            except Exception:  # noqa: BLE001
                dbg = repr(execution)[:4000]
        else:
            dbg = repr(execution)[:4000]
        context.log(f"[mcore_mcp] empty_response_body after_poll; execution_dump={dbg}")
        return {"error": "empty_response_body", "child_execution_id": ex_id, "child_status": _execution_status(execution)}

    if isinstance(raw, dict):
        out = raw
    else:
        try:
            out = json.loads(raw)
        except json.JSONDecodeError as e:
            return {"error": "invalid_json", "detail": str(e), "raw": str(raw)[:500]}
    if status_code >= 400:
        return {"error": "function_http_error", "upstream_status": status_code, "payload": out}
    return out


def main(context):  # noqa: ANN001 — Appwrite injects context type
    result: dict[str, Any]
    try:
        method = _request_method(context)
        data = _parse_json_body(context)
        context.log(f"[mcore_mcp] incoming_method={method} body_keys={list(data) if data else None}")

        if method == "GET":
            result = {
                "service": "mcore_mcp_gateway",
                "ok": True,
                "note": (
                    "This response is only for HTTP GET (health). To forward to "
                    "mcore_check_tree you must use HTTP POST with Content-Type: application/json "
                    "and a JSON object body (Console: set method POST, not GET)."
                ),
                "hint": (
                    'POST JSON: {"tool":"mcore_check_tree","arguments":{...}} '
                    'or {"op":"dna_encode",...} passthrough'
                ),
            }
        elif data is None:
            result = {
                "error": "JSON object body required",
                "detail": "Send Content-Type application/json with a JSON object, or wrapped {data: {...}}.",
            }
        else:
            tool = data.get("tool")
            if tool in ("mcore_check_tree", "check_tree", "check_tree_function"):
                payload = data.get("arguments")
                if not isinstance(payload, dict):
                    result = {"error": "arguments (object) required for tool calls"}
                else:
                    result = _forward_to_check_tree(context, payload)
            elif "op" in data:
                result = _forward_to_check_tree(context, data)
            else:
                result = {
                    "error": "unsupported_request",
                    "hint": (
                        'Use {"tool":"mcore_check_tree","arguments":{...}} '
                        'or {"op":"dna_encode",...}'
                    ),
                }
    except Exception:  # noqa: BLE001
        context.log(traceback.format_exc())
        context.error("mcore_mcp_gateway: unhandled exception")
        result = {"error": "internal_error"}

    context.log("=== mcore_mcp_gateway result ===")
    context.log(json.dumps(result, indent=2))
    return context.res.json(result)
