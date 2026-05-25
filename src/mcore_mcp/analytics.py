"""Optional PostHog analytics for MCP tool calls (server-side)."""

from __future__ import annotations

import atexit
import os
import uuid
from typing import Any

_client: Any = None


def _get_client() -> Any:
    global _client
    key = os.environ.get("POSTHOG_API_KEY")
    if not key:
        return None
    if _client is None:
        from posthog import Posthog

        host = os.environ.get("POSTHOG_HOST", "https://us.i.posthog.com")
        _client = Posthog(key, host=host)
    return _client


def capture_mcp_tool(
    tool: str,
    *,
    distinct_id: str | None = None,
    properties: dict[str, Any] | None = None,
) -> None:
    """Fire a lightweight product analytics event (verb + noun pattern)."""
    ph = _get_client()
    if not ph:
        return
    did = distinct_id or f"anonymous:{uuid.uuid4()}"
    ph.capture(
        distinct_id=did,
        event="mcore_mcp_tool_called",
        properties={"tool": tool, **(properties or {})},
    )


def capture_mcp_exception(
    tool: str,
    exc: BaseException,
    *,
    distinct_id: str | None = None,
) -> None:
    ph = _get_client()
    if not ph:
        return
    try:
        ph.capture_exception(
            exc,
            distinct_id=distinct_id or "anonymous",
            properties={"tool": tool},
        )
    except Exception:  # noqa: BLE001
        pass


def shutdown_analytics() -> None:
    global _client
    if _client is not None:
        try:
            _client.shutdown()
        except Exception:  # noqa: BLE001
            pass
        _client = None


atexit.register(shutdown_analytics)
