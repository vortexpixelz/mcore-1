"""FastMCP server: MCORE-1 + mcore_1 (DNA, bisection, GJB2 checks).

Run (stdio, default for Claude Desktop):

    python -m mcore_mcp.server

HTTP (gateway / Docker):

    python -m mcore_mcp.server --transport streamable-http --host 127.0.0.1 --port 8765

Optional: set ``APPWRITE_*`` and ``APPWRITE_USE_FUNCTIONS=true`` to delegate
``check_tree`` / DNA checks to the Appwrite Function in ``functions/check_tree``.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from typing import Annotated, Any

from fastmcp import FastMCP

from mcore_1.check_tree import check_deletion, check_tree
from mcore_1.encoder import dna_to_trits
from mcore_mcp import analytics
from mcore_mcp.delegate import delegate_check_tree
from mcore_py.algebra import OVERFLOW, enumerate_patterns, trit_add_seq
from mcore_py.checker import check_tree as check_constituent_tree
from mcore_py.cli import parse_pattern, trits_to_str
from mcore_py.model import Budget, Constituent, Level, ProsodicUnit, Trit

mcp = FastMCP(
    "MCORE-1",
    instructions=(
        "Metrical conservation (mcore_py), DNA carry + bisection trees (mcore_1). "
        "Tools mirror CLI capabilities plus stable check_tree / check_deletion APIs."
    ),
)


@mcp.tool(name="mcore_validate_metrical_pattern")
def mcore_validate_metrical_pattern(pattern: str) -> dict[str, Any]:
    """Validate a shorthand metrical pattern (012, -u-, Unicode morae, etc.)."""
    try:
        trits = parse_pattern(pattern)
        children = [ProsodicUnit(weight=t) for t in trits]
        pooled = trit_add_seq(trits)
        if pooled is OVERFLOW:
            analytics.capture_mcp_tool(
                "mcore_validate_metrical_pattern",
                properties={"ok": False, "reason": "overflow"},
            )
            return {"valid": False, "reason": "OVERFLOW", "pattern": pattern}
        parent = ProsodicUnit(weight=pooled, level=Level.L2_GANA)
        foot = Constituent(parent=parent, children=children)
        result = check_constituent_tree(foot)
        out = {
            "valid": result.valid,
            "pattern_classical": trits_to_str(trits),
            "total_weight": pooled.name,
            "errors": [{"kind": e.kind.name, "message": e.message} for e in result.errors],
        }
        analytics.capture_mcp_tool(
            "mcore_validate_metrical_pattern",
            properties={"ok": result.valid, "n": len(trits)},
        )
        return out
    except Exception as e:  # noqa: BLE001
        analytics.capture_mcp_exception("mcore_validate_metrical_pattern", e)
        raise


@mcp.tool(name="mcore_complete_pattern")
def mcore_complete_pattern(
    positions: Annotated[int, "Number of positions (matrae)."],
    budget: Annotated[int, "Trit ordinal 0=S1, 1=S2, 2=S3 for exact total weight."],
) -> dict[str, Any]:
    """Enumerate all valid length-n patterns whose total weight equals the budget."""
    try:
        b = Budget(
            min_weight=Trit(budget),
            max_weight=Trit(budget),
            unit=Level.L0_MATRA,
            exact=True,
        )
        patterns = enumerate_patterns(positions, b)
        data = [[t.value for t in p] for p in patterns]
        analytics.capture_mcp_tool(
            "mcore_complete_pattern",
            properties={"n": positions, "budget": budget, "count": len(patterns)},
        )
        return {"count": len(patterns), "patterns": data}
    except Exception as e:  # noqa: BLE001
        analytics.capture_mcp_exception("mcore_complete_pattern", e)
        raise


@mcp.tool(name="mcore_trit_sum_sequence")
def mcore_trit_sum_sequence(trits: list[int]) -> dict[str, Any]:
    """Pool trits (0,1,2) left-to-right; returns OVERFLOW on S3+S3."""
    try:
        ts = [Trit(t) for t in trits]
        pooled = trit_add_seq(ts)
        if pooled is OVERFLOW:
            analytics.capture_mcp_tool(
                "mcore_trit_sum_sequence",
                properties={"ok": False},
            )
            return {"ok": False, "result": "OVERFLOW"}
        analytics.capture_mcp_tool(
            "mcore_trit_sum_sequence",
            properties={"ok": True, "n": len(trits)},
        )
        return {"ok": True, "result": pooled.name, "ordinal": pooled.value}
    except Exception as e:  # noqa: BLE001
        analytics.capture_mcp_exception("mcore_trit_sum_sequence", e)
        raise


@mcp.tool(name="mcore_dna_to_trits")
def mcore_dna_to_trits(dna: str, include_log: bool = False) -> dict[str, Any]:
    """DNA carry encoder (A/C/G/T) to trits; optional per-step log."""
    try:
        trits, log = dna_to_trits(dna)
        out: dict[str, Any] = {"trits": trits, "length": len(trits)}
        if include_log:
            out["log"] = [asdict(s) for s in log]
        analytics.capture_mcp_tool(
            "mcore_dna_to_trits",
            properties={"length": len(trits), "log": include_log},
        )
        return out
    except Exception as e:  # noqa: BLE001
        analytics.capture_mcp_exception("mcore_dna_to_trits", e)
        raise


@mcp.tool(name="mcore_check_tree_weights")
def mcore_check_tree_weights(
    weights: list[int],
    depth: int | None = None,
) -> dict[str, Any]:
    """Stable bisection check on leaf weights 0..2 (internal nodes only)."""
    try:
        remote = delegate_check_tree("check_tree_weights", {"weights": weights, "depth": depth})
        if remote is not None:
            analytics.capture_mcp_tool(
                "mcore_check_tree_weights",
                properties={"delegated": True, "n": len(weights)},
            )
            return remote
        nodes = check_tree(weights, depth=depth)
        rows = [asdict(n) for n in nodes]
        analytics.capture_mcp_tool(
            "mcore_check_tree_weights",
            properties={
                "delegated": False,
                "n": len(weights),
                "all_valid": all(n.valid for n in nodes),
            },
        )
        return {"nodes": rows}
    except Exception as e:  # noqa: BLE001
        analytics.capture_mcp_exception("mcore_check_tree_weights", e)
        raise


@mcp.tool(name="mcore_check_tree_dna")
def mcore_check_tree_dna(dna: str, depth: int | None = None) -> dict[str, Any]:
    """Encode DNA then run bisection check_tree (HANDOFF_TO_GJB2 semantics)."""
    try:
        remote = delegate_check_tree("check_tree_dna", {"dna": dna, "depth": depth})
        if remote is not None:
            analytics.capture_mcp_tool(
                "mcore_check_tree_dna",
                properties={"delegated": True, "length": len(dna)},
            )
            return remote
        trits, _log = dna_to_trits(dna)
        nodes = check_tree(trits, depth=depth)
        rows = [asdict(n) for n in nodes]
        analytics.capture_mcp_tool(
            "mcore_check_tree_dna",
            properties={
                "delegated": False,
                "length": len(dna),
                "all_valid": all(n.valid for n in nodes),
            },
        )
        return {"trits": trits, "nodes": rows}
    except Exception as e:  # noqa: BLE001
        analytics.capture_mcp_exception("mcore_check_tree_dna", e)
        raise


@mcp.tool(name="mcore_check_deletion")
def mcore_check_deletion(
    weights_wt: list[int],
    weights_mut: list[int],
    deletion_pos_1: int,
) -> dict[str, Any]:
    """WT vs mutant trit streams after single-base deletion (frozen topology)."""
    try:
        remote = delegate_check_tree(
            "check_deletion",
            {
                "weights_wt": weights_wt,
                "weights_mut": weights_mut,
                "deletion_pos_1": deletion_pos_1,
            },
        )
        if remote is not None:
            analytics.capture_mcp_tool("mcore_check_deletion", properties={"delegated": True})
            return remote
        nodes = check_deletion(weights_wt, weights_mut, deletion_pos_1)
        rows = [asdict(n) for n in nodes]
        analytics.capture_mcp_tool(
            "mcore_check_deletion",
            properties={"delegated": False, "all_valid": all(n.valid for n in nodes)},
        )
        return {"nodes": rows}
    except Exception as e:  # noqa: BLE001
        analytics.capture_mcp_exception("mcore_check_deletion", e)
        raise


@mcp.tool(name="mcore_appwrite_exec_check_tree")
def mcore_appwrite_exec_check_tree(body_json: str) -> dict[str, Any]:
    """Execute the Appwrite check_tree function; body JSON with op (see function README)."""
    from mcore_appwrite.config import AppwriteConfig
    from mcore_appwrite.executor import execute_check_tree_function

    cfg = AppwriteConfig.from_env()
    if not cfg or not cfg.check_tree_function_id:
        return {"error": "Appwrite function not configured (APPWRITE_* / FUNCTION id)."}
    try:
        body = json.loads(body_json)
    except json.JSONDecodeError as e:
        return {"error": f"invalid json: {e}"}
    if not isinstance(body, dict):
        return {"error": "body must be a JSON object"}
    try:
        out = execute_check_tree_function(cfg, body)
        ok = "error" not in out
        analytics.capture_mcp_tool("mcore_appwrite_exec_check_tree", properties={"ok": ok})
        return out
    except Exception as e:  # noqa: BLE001
        analytics.capture_mcp_exception("mcore_appwrite_exec_check_tree", e)
        raise


def main() -> None:
    p = argparse.ArgumentParser(description="MCORE-1 FastMCP server")
    p.add_argument(
        "--transport",
        default="stdio",
        choices=("stdio", "streamable-http"),
        help="MCP transport (default stdio for desktop)",
    )
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    args = p.parse_args()
    if args.transport == "stdio":
        mcp.run()
    else:
        mcp.run(transport="streamable-http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
