"""Smoke tests for FastMCP tool registration (requires ``[mcp]`` extra)."""

from __future__ import annotations

import pytest

pytest.importorskip("fastmcp")

from mcore_mcp import server as mcp_server  # noqa: E402


def test_validate_tool_smoke() -> None:
    out = mcp_server.mcore_validate_metrical_pattern("01")
    assert out["valid"] is True


def test_check_tree_two_leaves() -> None:
    out = mcp_server.mcore_check_tree_weights([0, 1], depth=1)
    assert "nodes" in out
    assert len(out["nodes"]) == 1
    assert out["nodes"][0]["valid"] is True
