"""
solar_conservation_audit.py
============================
Pipes solar_ingestor quantize_to_trits() -> weights_for_check_tree()
into the deployed Appwrite check_tree function (or mcore_1 locally),
then logs CONSERVATION / OVERFLOW error density at PIL boundary nodes.

Execution modes
---------------
Remote (Appwrite Functions):
    export APPWRITE_ENDPOINT=https://cloud.appwrite.io/v1
    export APPWRITE_PROJECT_ID=<your-project-id>
    export APPWRITE_API_KEY=<your-api-key>
    export APPWRITE_FUNCTION_CHECK_TREE_ID=<function-id>
    export APPWRITE_USE_FUNCTIONS=true
    python solar_conservation_audit.py

Local (no Appwrite needed — uses mcore_1 directly):
    python solar_conservation_audit.py --local

With real FITS data:
    python solar_conservation_audit.py path/to/hmi.fits --local

Output
------
Per-node table:
  [node_id]  leaves [lo…hi]  [PIL]  OK/FAIL  errors

Summary:
  Total nodes | Conservation errors | Overflow errors
  PIL boundary breakdown | global density | PIL density

Dumps: solar_audit_result.json  (pipe into whitepaper empirical table)

CLAIM STATUS
------------
[ESTABLISHED]  weights_for_check_tree shift: t+1 for t in {-1,0,+1} -> {0,1,2}
[ESTABLISHED]  check_tree payload contract {"weights": list[int in {0,1,2}]}
[ESTABLISHED]  NodeResult fields: node_id, leaf_lo, leaf_hi, valid, errors
[PLAUSIBLE]    PIL boundary error density > global => carry-cascade stress
               localizes at polarity inversion (tearing-mode analog)
[CONJECTURAL]  Conservation violations map to physically meaningful tearing events
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from solar_ingestor import fetch_solar_slice, quantize_to_trits, weights_for_check_tree


# ---------------------------------------------------------------------------
# Audit node (mirrors mcore_1.check_tree.NodeResult)
# ---------------------------------------------------------------------------

@dataclass
class AuditNode:
    node_id: str
    leaf_lo: int
    leaf_hi: int
    valid: bool
    errors: list[str]

    @property
    def has_conservation(self) -> bool:
        return "CONSERVATION" in self.errors

    @property
    def has_overflow(self) -> bool:
        return "OVERFLOW" in self.errors


# ---------------------------------------------------------------------------
# Remote: Appwrite Functions
# ---------------------------------------------------------------------------

def run_remote(weights: list[int]) -> list[AuditNode]:
    """Call the deployed Appwrite check_tree Function.

    Payload:  {"weights": [0|1|2, ...]}
    Response: {"nodes": [{"node_id", "leaf_lo", "leaf_hi", "valid", "errors"}, ...]}
    """
    try:
        from mcore_appwrite.config import AppwriteConfig
        from mcore_appwrite.executor import execute_check_tree_function
    except ImportError as exc:
        raise SystemExit(
            f"[remote] mcore_appwrite not importable: {exc}\n"
            "Run from the repo root or: pip install -e .[dev]\n"
            "Use --local to skip Appwrite entirely."
        ) from exc

    cfg = AppwriteConfig.from_env()
    if cfg is None:
        raise SystemExit(
            "[remote] Missing env vars.\n"
            "Required: APPWRITE_ENDPOINT, APPWRITE_PROJECT_ID, APPWRITE_API_KEY\n"
            "Optional: APPWRITE_FUNCTION_CHECK_TREE_ID\n"
            "Use --local to skip Appwrite entirely."
        )

    payload: dict[str, Any] = {"weights": weights}
    print(
        f"[remote] Sending {len(weights)} weights to Appwrite function "
        f"'{cfg.check_tree_function_id}' ..."
    )
    response = execute_check_tree_function(cfg, payload)

    if "error" in response:
        raise SystemExit(f"[remote] Function returned error: {response}")

    nodes_raw: list[dict[str, Any]] = response.get("nodes", [])
    return [
        AuditNode(
            node_id=n["node_id"],
            leaf_lo=n["leaf_lo"],
            leaf_hi=n["leaf_hi"],
            valid=n["valid"],
            errors=n.get("errors", []),
        )
        for n in nodes_raw
    ]


# ---------------------------------------------------------------------------
# Local: mcore_1 direct call
# ---------------------------------------------------------------------------

def run_local(weights: list[int]) -> list[AuditNode]:
    """Call mcore_1.check_tree directly — no Appwrite credentials needed."""
    try:
        from mcore_1.check_tree import check_tree as _check_tree
    except ImportError as exc:
        raise SystemExit(
            f"[local] mcore_1 not importable: {exc}\n"
            "Install with: pip install -e .[dev] from the repo root."
        ) from exc

    return [
        AuditNode(
            node_id=nr.node_id,
            leaf_lo=nr.leaf_lo,
            leaf_hi=nr.leaf_hi,
            valid=nr.valid,
            errors=list(nr.errors),
        )
        for nr in _check_tree(weights)
    ]


# ---------------------------------------------------------------------------
# PIL boundary detection
# ---------------------------------------------------------------------------

def detect_pil_boundary(trits: list[int]) -> tuple[int, int]:
    """Return (last_positive_0idx, first_negative_0idx).

    PIL boundary nodes are internal tree nodes whose [leaf_lo, leaf_hi]
    span straddles this transition. Returns (-1, -1) if no clear inversion.
    """
    last_pos = max((i for i, t in enumerate(trits) if t == 1), default=-1)
    first_neg = next((i for i, t in enumerate(trits) if t == -1), -1)
    return last_pos, first_neg


def is_pil_boundary_node(node: AuditNode, last_pos: int, first_neg: int) -> bool:
    """True when the node's 0-based leaf span straddles the +/- inversion."""
    if last_pos < 0 or first_neg < 0:
        return False
    lo0 = node.leaf_lo - 1   # check_tree uses 1-based leaf indices
    hi0 = node.leaf_hi - 1
    return lo0 <= last_pos <= hi0 or lo0 <= first_neg <= hi0


# ---------------------------------------------------------------------------
# Main audit runner
# ---------------------------------------------------------------------------

def run_audit(
    fits_path: str | None = None,
    noise_floor: float = 50.0,
    mode: str = "auto",
) -> None:
    print("=" * 65)
    print("MCORE-1 Solar Conservation Audit")
    print("=" * 65)

    # 1. Ingest & quantize
    solar_flux = fetch_solar_slice(fits_path)
    trits = quantize_to_trits(solar_flux, noise_floor=noise_floor)
    weights = weights_for_check_tree(trits)

    dist = {k: trits.count(k) for k in (-1, 0, 1)}
    print(f"\nQuantized {len(trits)} cells:  +1={dist[1]}  0={dist[0]}  -1={dist[-1]}")
    print(f"Weights (0/1/2):  {weights}")

    # 2. PIL boundary
    last_pos, first_neg = detect_pil_boundary(trits)
    if last_pos >= 0 and first_neg >= 0:
        print(
            f"\nPIL boundary: last +1 at cell {last_pos}, "
            f"first -1 at cell {first_neg}"
        )
    else:
        print("\nNo clear PIL polarity inversion in this slice.")

    # 3. Execution mode
    use_remote = (
        mode == "remote"
        or (
            mode == "auto"
            and os.environ.get("APPWRITE_USE_FUNCTIONS", "").lower()
            in ("1", "true", "yes")
        )
    )
    label = "remote → Appwrite Functions" if use_remote else "local → mcore_1"
    print(f"\nRunning check_tree [{label}] ...")

    nodes = run_remote(weights) if use_remote else run_local(weights)

    if not nodes:
        print(
            "\ncheck_tree returned 0 internal nodes.\n"
            "Sequence may be too short to build a bisection tree (need >= 2 leaves)."
        )
        return

    # 4. Per-node table
    print(f"\n{'NODE':>22}  {'LEAVES':>10}  {'PIL':>4}  {'STATUS':>6}  ERRORS")
    print("-" * 65)
    for n in nodes:
        is_pil = is_pil_boundary_node(n, last_pos, first_neg)
        pil_tag = " PIL" if is_pil else "    "
        status = "OK  " if n.valid else "FAIL"
        errs = ", ".join(n.errors) if n.errors else "—"
        print(
            f"  {n.node_id:>20}  [{n.leaf_lo:>3}…{n.leaf_hi:<3}]{pil_tag}  "
            f"{status}  {errs}"
        )

    # 5. Summary statistics
    total = len(nodes)
    pil_nodes = [n for n in nodes if is_pil_boundary_node(n, last_pos, first_neg)]
    c_total = sum(1 for n in nodes if n.has_conservation)
    o_total = sum(1 for n in nodes if n.has_overflow)
    c_pil   = sum(1 for n in pil_nodes if n.has_conservation)
    o_pil   = sum(1 for n in pil_nodes if n.has_overflow)

    global_density = (c_total + o_total) / total
    pil_density    = (c_pil + o_pil) / len(pil_nodes) if pil_nodes else 0.0

    print("\n" + "=" * 65)
    print("SUMMARY")
    print("-" * 65)
    print(f"  Total internal nodes       : {total}")
    print(f"  PIL boundary nodes         : {len(pil_nodes)}")
    print(f"  CONSERVATION errors        : {c_total}  (PIL: {c_pil})")
    print(f"  OVERFLOW errors            : {o_total}  (PIL: {o_pil})")
    print(f"  Global error density       : {global_density:.4f}")
    print(f"  PIL boundary error density : {pil_density:.4f}")
    print("=" * 65)

    # 6. Honest interpretation
    print("\nINTERPRETATION  [claim tier in brackets]")
    if pil_density > global_density:
        print(
            f"  [PLAUSIBLE] PIL density ({pil_density:.4f}) > global ({global_density:.4f}).\n"
            "  Carry-cascade stress localizes at polarity inversion — consistent\n"
            "  with discrete tearing-mode instability analog.\n"
            "  Quantitative MHD/PIC validation required to promote to [ESTABLISHED]."
        )
    elif global_density == 0.0:
        print(
            "  [ESTABLISHED] Conservation holds across ALL nodes.\n"
            "  The mora-pooling invariant is satisfied end-to-end for this slice.\n"
            "  (Expected for short synthetic slices without deep shear gradients.)"
        )
    else:
        print(
            f"  [PLAUSIBLE] Global density ({global_density:.4f}) >= PIL density ({pil_density:.4f}).\n"
            "  Errors distributed uniformly — no preferential PIL localization.\n"
            "  Consider adjusting --noise-floor or using a longer sequence."
        )

    # 7. JSON dump
    out = {
        "trits": trits,
        "weights": weights,
        "pil_boundary": {"last_pos_0idx": last_pos, "first_neg_0idx": first_neg},
        "nodes": [
            {
                "node_id": n.node_id,
                "leaf_lo": n.leaf_lo,
                "leaf_hi": n.leaf_hi,
                "valid": n.valid,
                "errors": n.errors,
                "is_pil_boundary": is_pil_boundary_node(n, last_pos, first_neg),
            }
            for n in nodes
        ],
        "summary": {
            "total_nodes": total,
            "pil_nodes": len(pil_nodes),
            "conservation_errors": c_total,
            "overflow_errors": o_total,
            "pil_conservation_errors": c_pil,
            "pil_overflow_errors": o_pil,
            "global_error_density": round(global_density, 6),
            "pil_error_density": round(pil_density, 6),
        },
    }
    json_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "solar_audit_result.json"
    )
    with open(json_path, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\nFull audit JSON -> {json_path}")
    print("(Pipe solar_audit_result.json into the whitepaper empirical results table.)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCORE-1 Solar Conservation Audit")
    parser.add_argument(
        "fits_path",
        nargs="?",
        default=None,
        help="Path to SDO/HMI FITS file (uses synthetic PIL slice if omitted)",
    )
    parser.add_argument(
        "--noise-floor",
        type=float,
        default=50.0,
        help="Quantization threshold epsilon in Gauss (default: 50.0)",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Force local mcore_1 execution (bypass Appwrite even if env vars set)",
    )
    parser.add_argument(
        "--remote",
        action="store_true",
        help="Force remote Appwrite Functions execution",
    )
    args = parser.parse_args()

    if args.local and args.remote:
        parser.error("Cannot specify both --local and --remote.")

    mode = "local" if args.local else "remote" if args.remote else "auto"
    run_audit(fits_path=args.fits_path, noise_floor=args.noise_floor, mode=mode)
