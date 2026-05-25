"""MCP overlay + acoustic tools (requires ``[mcp]`` + ``[analysis]`` extras)."""

from __future__ import annotations

import pytest

pytest.importorskip("numpy")
pytest.importorskip("fastmcp")

from mcore_mcp import server as mcp_server  # noqa: E402


def test_methylation_island_tool() -> None:
    out = mcp_server.mcore_methylation_island_check([0.05, 0.10, 0.08])
    assert out["valid"] is True


def test_quantum_frame_tool() -> None:
    out = mcp_server.mcore_quantum_frame_check([0.95])
    assert out["valid"] is True


def test_acoustic_summary_tool() -> None:
    out = mcp_server.mcore_acoustic_phonon_synthesis_summary([0, 1, 2])
    assert out["n_atoms"] == 3
    assert out["sample_rate_hz"] == 48_000
