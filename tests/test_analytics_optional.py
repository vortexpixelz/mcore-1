"""Optional PostHog helper does not require SDK at import time."""

from __future__ import annotations

from mcore_mcp import analytics


def test_capture_without_posthog_env() -> None:
    analytics.capture_mcp_tool("test_tool", properties={"n": 1})
    analytics.shutdown_analytics()
