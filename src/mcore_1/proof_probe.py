"""Experimental proof-chain corruption probe for MCORE-1.

This module is a calibration harness, not a complexity-theory result. It builds a
small locally checkable resolution proof, forges one provenance edge while keeping
the derived clause unchanged, and asks whether a frozen MCORE tree localizes the
structural disturbance.

Claim boundary: certificate-auditing benchmark only; no inference about P vs NP.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from mcore_1.check_tree import check_constituent
from mcore_1.tree import (
    _pooled_orig_trits_on_topology,
    build_binary_metrical_tree,
    descendant_orig_indices,
)
from mcore_py.model import Constituent


Clause = tuple[int, ...]


@dataclass(frozen=True)
class ResolutionStep:
    """One locally checkable binary-resolution inference."""

    sid: int
    clause: Clause
    left: int
    right: int
    pivot: int


def _canonical_clause(literals: set[int]) -> Clause:
    return tuple(sorted(literals, key=lambda lit: (abs(lit), lit < 0)))


def resolve_clause(left: Clause, right: Clause, pivot: int) -> Clause | None:
    """Return the binary resolvent on pivot, or None if the edge is invalid."""

    lhs = set(left)
    rhs = set(right)
    if pivot in lhs and -pivot in rhs:
        pass
    elif -pivot in lhs and pivot in rhs:
        pass
    else:
        return None

    out = (lhs | rhs) - {pivot, -pivot}
    if any(-lit in out for lit in out):
        return None
    return _canonical_clause(out)


def make_implication_chain(n: int = 12) -> tuple[dict[int, Clause], list[ResolutionStep]]:
    """Build a tiny UNSAT chain with a deterministic resolution certificate."""

    if n < 4:
        raise ValueError("n must be at least 4")

    clauses: dict[int, Clause] = {1: (1,)}
    for i in range(1, n):
        clauses[i + 1] = (-i, i + 1)
    clauses[n + 1] = (-n,)

    steps: list[ResolutionStep] = []
    previous = 1
    sid = n + 2
    for i in range(1, n):
        step = ResolutionStep(
            sid=sid,
            clause=(i + 1,),
            left=previous,
            right=i + 1,
            pivot=i,
        )
        clauses[sid] = step.clause
        steps.append(step)
        previous = sid
        sid += 1

    final = ResolutionStep(
        sid=sid,
        clause=(),
        left=previous,
        right=n + 1,
        pivot=n,
    )
    steps.append(final)
    return clauses, steps


def verify_resolution_proof(
    initial: dict[int, Clause],
    steps: list[ResolutionStep],
) -> tuple[bool, int | None]:
    """Check each inference in order; return (valid, first_bad_step_id)."""

    known = dict(initial)
    for step in steps:
        if step.left not in known or step.right not in known:
            return False, step.sid
        resolvent = resolve_clause(known[step.left], known[step.right], step.pivot)
        if resolvent != _canonical_clause(set(step.clause)):
            return False, step.sid
        known[step.sid] = step.clause

    if not steps or steps[-1].clause != ():
        return False, steps[-1].sid if steps else None
    return True, None


def forge_parent_reference(
    steps: list[ResolutionStep],
    *,
    step_index_1: int = 6,
) -> list[ResolutionStep]:
    """Forge one justification edge while preserving every conclusion."""

    if step_index_1 < 3 or step_index_1 > len(steps):
        raise ValueError("step_index_1 must be in [3, len(steps)]")

    out = list(steps)
    idx = step_index_1 - 1
    replacement_parent = steps[idx - 2].sid
    out[idx] = replace(out[idx], left=replacement_parent)
    return out


def step_to_trit(step: ResolutionStep) -> int:
    """Map a proof-line checksum to 0, 1, or 2 without using a validity label."""

    literal_term = sum(2 * abs(lit) + (1 if lit < 0 else 0) for lit in step.clause)
    return (literal_term + step.left + 2 * step.right + step.pivot) % 3


def _error_spans(root: Constituent) -> set[tuple[int, int, str]]:
    result = check_constituent(root)
    id_to_span: dict[str, tuple[int, int]] = {}

    def walk(node: Constituent) -> None:
        for child in node.children:
            if isinstance(child, Constituent):
                walk(child)
        indices = descendant_orig_indices(node)
        id_to_span[node.parent.id] = (indices[0], indices[-1])

    walk(root)
    return {
        (*id_to_span[error.node_id], error.kind.name)
        for error in result.errors
        if error.node_id in id_to_span
    }


def mcore_delta_error_spans(
    baseline_weights: list[int],
    forged_weights: list[int],
) -> list[tuple[int, int, str]]:
    """Return checker errors introduced by a same-length forged weight stream."""

    if not baseline_weights or len(baseline_weights) != len(forged_weights):
        raise ValueError("weight streams must be non-empty and have equal length")

    indices = list(range(1, len(baseline_weights) + 1))
    baseline_root = build_binary_metrical_tree(baseline_weights, indices)
    forged_root = build_binary_metrical_tree(forged_weights, indices)
    if not isinstance(baseline_root, Constituent) or not isinstance(forged_root, Constituent):
        raise ValueError("probe requires at least two proof steps")

    baseline_errors = _error_spans(baseline_root)

    _pooled_orig_trits_on_topology(forged_root, baseline_weights)
    forged_errors = _error_spans(forged_root)

    return sorted(forged_errors - baseline_errors, key=lambda row: (row[1] - row[0], row))


def run_pilot(*, n: int = 12, forge_step_index: int = 6) -> dict[str, object]:
    """Run the deterministic counterfeit-receipt calibration and return a receipt."""

    all_clauses, intact_steps = make_implication_chain(n)
    input_clause_count = n + 1
    initial = {
        cid: clause
        for cid, clause in all_clauses.items()
        if cid <= input_clause_count
    }

    intact_ok, intact_bad = verify_resolution_proof(initial, intact_steps)
    forged_steps = forge_parent_reference(intact_steps, step_index_1=forge_step_index)
    forged_ok, forged_bad = verify_resolution_proof(initial, forged_steps)

    intact_weights = [step_to_trit(step) for step in intact_steps]
    forged_weights = [step_to_trit(step) for step in forged_steps]
    changed_positions = [
        i
        for i, (intact, forged) in enumerate(
            zip(intact_weights, forged_weights, strict=True),
            1,
        )
        if intact != forged
    ]

    delta_errors = mcore_delta_error_spans(intact_weights, forged_weights)
    if delta_errors:
        min_width = min(hi - lo for lo, hi, _ in delta_errors)
        narrowest = [
            (lo, hi, kind)
            for lo, hi, kind in delta_errors
            if hi - lo == min_width
        ]
    else:
        narrowest = []

    forge_sid = intact_steps[forge_step_index - 1].sid
    span_contains_forge = bool(narrowest) and all(
        lo <= forge_step_index <= hi for lo, hi, _ in narrowest
    )
    exact_edge_from_frozen_leaf_delta = (
        changed_positions[0] if len(changed_positions) == 1 else None
    )

    return {
        "benchmark": "MINT-GLACIER-847291 // counterfeit receipt // proof-chain localization",
        "claim_boundary": "MCORE certificate-auditing benchmark; not evidence about P vs NP",
        "proof_steps": len(intact_steps),
        "forge_step_index": forge_step_index,
        "forge_step_id": forge_sid,
        "intact_verifies": intact_ok,
        "intact_first_bad_step_id": intact_bad,
        "forged_verifies": forged_ok,
        "verifier_first_bad_step_id": forged_bad,
        "changed_trit_positions": changed_positions,
        "mcore_delta_errors": delta_errors,
        "mcore_narrowest_spans": narrowest,
        "mcore_span_contains_forge": span_contains_forge,
        "exact_edge_from_frozen_leaf_delta": exact_edge_from_frozen_leaf_delta,
    }


__all__ = [
    "Clause",
    "ResolutionStep",
    "forge_parent_reference",
    "make_implication_chain",
    "mcore_delta_error_spans",
    "resolve_clause",
    "run_pilot",
    "step_to_trit",
    "verify_resolution_proof",
]
