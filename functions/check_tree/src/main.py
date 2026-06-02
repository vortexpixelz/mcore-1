"""Appwrite Function: MCORE check_tree + DNA carry (mcore_1).

Deployment must include ``mcore_src/mcore_py`` and ``mcore_src/mcore_1`` — see
``functions/check_tree/README.md``.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from dataclasses import asdict
from pathlib import Path


def _ensure_mcore_on_path() -> None:
    here = Path(__file__).resolve().parent
    roots = [
        here.parent / "mcore_src",  # bundled layout
        here.parent.parent.parent / "src",  # monorepo dev: functions/check_tree/src -> repo/src
    ]
    for r in roots:
        if (r / "mcore_1").is_dir() and str(r) not in sys.path:
            sys.path.insert(0, str(r))
            return
    raise RuntimeError(
        "mcore_1 not found: vendor src/mcore_1 and src/mcore_py into mcore_src/ "
        "before deploying (see functions/check_tree/README.md)."
    )


def _posthog_capture(event: str, properties: dict[str, object]) -> None:
    key = os.environ.get("POSTHOG_API_KEY")
    if not key:
        return
    try:
        from posthog import Posthog

        host = os.environ.get("POSTHOG_HOST", "https://us.i.posthog.com")
        ph = Posthog(key, host=host)
        ph.capture(
            distinct_id="appwrite_function_mcore_check_tree",
            event=event,
            properties=properties,
        )
        ph.shutdown()
    except Exception:  # noqa: BLE001 — never fail the function on telemetry
        pass


def _node_results_to_json(nodes: list[object]) -> list[dict[str, object]]:
    return [asdict(n) for n in nodes]  # type: ignore[arg-type]


def main(context):  # noqa: ANN001 — Appwrite injects context type
    _ensure_mcore_on_path()
    from mcore_1.check_tree import check_deletion, check_tree
    from mcore_1.encoder import dna_to_trits

    result: dict[str, object]

    try:
        if context.req.method == "GET":
            result = {"service": "mcore_check_tree", "ok": True}
        else:
            data = context.req.body_json
            if not isinstance(data, dict):
                result = {"error": "JSON object body required"}
            else:
                op = data.get("op")
                if op == "dna_encode":
                    dna = data.get("dna")
                    if not isinstance(dna, str) or not dna:
                        result = {"error": "dna (non-empty string) required"}
                    else:
                        trits, log = dna_to_trits(dna)
                        result = {
                            "trits": trits,
                            "log": [asdict(s) for s in log],
                        }
                        _posthog_capture(
                            "appwrite_function_check_tree",
                            {"op": op, "dna_length": len(dna)},
                        )
                elif op == "check_tree_weights":
                    weights = data.get("weights")
                    if not isinstance(weights, list):
                        result = {"error": "weights (list[int]) required"}
                    else:
                        depth = data.get("depth")
                        d: int | None = None if depth is None else int(depth)
                        nodes = check_tree([int(w) for w in weights], depth=d)
                        _posthog_capture(
                            "appwrite_function_check_tree",
                            {
                                "op": op,
                                "n": len(weights),
                                "all_valid": all(n.valid for n in nodes),
                            },
                        )
                        result = {"nodes": _node_results_to_json(nodes)}
                elif op == "check_tree_dna":
                    dna = data.get("dna")
                    if not isinstance(dna, str) or not dna:
                        result = {"error": "dna (non-empty string) required"}
                    else:
                        depth = data.get("depth")
                        d = None if depth is None else int(depth)
                        trits, _log = dna_to_trits(dna)
                        nodes = check_tree(trits, depth=d)
                        _posthog_capture(
                            "appwrite_function_check_tree",
                            {
                                "op": op,
                                "n": len(trits),
                                "all_valid": all(n.valid for n in nodes),
                            },
                        )
                        result = {"trits": trits, "nodes": _node_results_to_json(nodes)}
                elif op == "check_deletion":
                    wt = data.get("weights_wt")
                    mut = data.get("weights_mut")
                    k = data.get("deletion_pos_1")
                    if not isinstance(wt, list) or not isinstance(mut, list):
                        result = {
                            "error": "weights_wt and weights_mut (lists) required",
                        }
                    elif not isinstance(k, int):
                        result = {"error": "deletion_pos_1 (int) required"}
                    else:
                        nodes = check_deletion([int(x) for x in wt], [int(x) for x in mut], k)
                        _posthog_capture(
                            "appwrite_function_check_tree",
                            {
                                "op": op,
                                "n_wt": len(wt),
                                "all_valid": all(n.valid for n in nodes),
                            },
                        )
                        result = {"nodes": _node_results_to_json(nodes)}
                else:
                    result = {"error": f"unknown op: {op!r}"}

    except ValueError as e:
        _posthog_capture("appwrite_function_check_tree_error", {"kind": "ValueError"})
        result = {"error": str(e)}
    except Exception:  # noqa: BLE001
        context.log(traceback.format_exc())
        _posthog_capture("appwrite_function_check_tree_error", {"kind": "internal"})
        result = {"error": "internal_error"}

    context.log("=== mcore_check_tree result ===")
    context.log(json.dumps(result, indent=2))
    # Do not pass HTTP status as 2nd arg — some Open Runtimes drop the body (empty responseBody).
    return context.res.json(result)
