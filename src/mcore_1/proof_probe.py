"""Experimental proof-chain corruption probes for MCORE-1.

This module is a calibration harness, not a complexity-theory result. It builds a
small locally checkable resolution proof, forges one provenance edge while keeping
the derived clause unchanged, and compares two frozen MCORE adapters:

V1: compress each proof line to one trit.
V2: represent each inference as a local ordered provenance constituent whose
    children encode graph-theoretic edge spans.

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
from mcore_py.algebra import OVERFLOW, trit_add
from mcore_py.model import Constituent, Level, ProsodicUnit, Trit


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


# ---------------------------------------------------------------------------
# V1: scalar proof-line adapter
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# V2: topology-native local provenance constituents
# ---------------------------------------------------------------------------


def _derived_step_positions(steps: list[ResolutionStep]) -> dict[int, int]:
    return {step.sid: index for index, step in enumerate(steps, 1)}


def _edge_span_trit(
    parent_id: int,
    *,
    current_index: int,
    derived_positions: dict[int, int],
) -> Trit:
    """Quantize a proof edge by backward span in the derived-step topology.

    Input-clause references and immediate-predecessor derived references are S1.
    A one-step skip is S2. Longer skips are S3.

    This is a graph feature, not a validity label. The calibration forge changes
    only one left edge from immediate predecessor to a one-step skip.
    """

    parent_index = derived_positions.get(parent_id)
    if parent_index is None:
        return Trit.S1

    span = current_index - parent_index
    if span <= 1:
        return Trit.S1
    if span == 2:
        return Trit.S2
    return Trit.S3


def _provenance_constituent(
    baseline_step: ResolutionStep,
    observed_step: ResolutionStep,
    *,
    step_index: int,
    baseline_positions: dict[int, int],
) -> Constituent:
    """Build one frozen local proof-provenance constituent.

    The parent weight is declared by the intact edge topology. The children are
    the observed proof's left/right provenance edges.
    """

    baseline_left = _edge_span_trit(
        baseline_step.left,
        current_index=step_index,
        derived_positions=baseline_positions,
    )
    baseline_right = _edge_span_trit(
        baseline_step.right,
        current_index=step_index,
        derived_positions=baseline_positions,
    )
    frozen_parent = trit_add(baseline_left, baseline_right)
    if frozen_parent is OVERFLOW:
        raise ValueError(
            f"baseline topology overflows at proof step {step_index}; "
            "choose a calibration whose intact local gadget is representable"
        )

    observed_left = _edge_span_trit(
        observed_step.left,
        current_index=step_index,
        derived_positions=baseline_positions,
    )
    observed_right = _edge_span_trit(
        observed_step.right,
        current_index=step_index,
        derived_positions=baseline_positions,
    )

    parent = ProsodicUnit(
        weight=frozen_parent,
        level=Level.L1_AKSARA,
        label=f"proof-step:{baseline_step.sid}",
    )
    parent.features["proof_step_index"] = step_index
    parent.features["proof_step_id"] = baseline_step.sid
    parent.features["adapter"] = "proof-edge-span-v2"

    left = ProsodicUnit(
        weight=observed_left,
        level=Level.L0_MATRA,
        label=f"left-parent:{observed_step.left}",
    )
    left.features["proof_parent_id"] = observed_step.left
    left.features["edge_role"] = "left"

    right = ProsodicUnit(
        weight=observed_right,
        level=Level.L0_MATRA,
        label=f"right-parent:{observed_step.right}",
    )
    right.features["proof_parent_id"] = observed_step.right
    right.features["edge_role"] = "right"

    return Constituent(parent=parent, children=[left, right])


def topology_provenance_errors(
    baseline_steps: list[ResolutionStep],
    observed_steps: list[ResolutionStep],
) -> list[dict[str, object]]:
    """Return local MCORE checker errors for topology differences."""

    if len(baseline_steps) != len(observed_steps):
        raise ValueError("baseline and observed proof chains must have equal length")

    baseline_positions = _derived_step_positions(baseline_steps)
    errors: list[dict[str, object]] = []

    for index, (baseline, observed) in enumerate(
        zip(baseline_steps, observed_steps, strict=True),
        1,
    ):
        if baseline.sid != observed.sid or baseline.clause != observed.clause:
            raise ValueError(
                "topology probe requires stable step ids and conclusions; "
                "only provenance edges may differ"
            )

        gadget = _provenance_constituent(
            baseline,
            observed,
            step_index=index,
            baseline_positions=baseline_positions,
        )
        result = check_constituent(gadget)
        if result.errors:
            errors.append(
                {
                    "step_index": index,
                    "step_id": baseline.sid,
                    "left_parent": observed.left,
                    "right_parent": observed.right,
                    "error_kinds": sorted({error.kind.name for error in result.errors}),
                }
            )

    return errors


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

    v2_intact_errors = topology_provenance_errors(intact_steps, intact_steps)
    v2_forged_errors = topology_provenance_errors(intact_steps, forged_steps)
    v2_error_steps = [int(row["step_index"]) for row in v2_forged_errors]

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
        "v1_mcore_delta_errors": delta_errors,
        "v1_mcore_narrowest_spans": narrowest,
        "v1_mcore_span_contains_forge": span_contains_forge,
        "exact_edge_from_frozen_leaf_delta": exact_edge_from_frozen_leaf_delta,
        "v2_intact_errors": v2_intact_errors,
        "v2_forged_errors": v2_forged_errors,
        "v2_error_steps": v2_error_steps,
        "v2_exact_localization": v2_error_steps == [forge_step_index],
    }


__all__ = [
    "Clause",
    "ResolutionStep",
    "forge_parent_reference",
    "make_implication_chain",
    "mcore_delta_error_spans",
    "resolve_clause",
    "run_pilot",
    "run_strong_counterfeit",
    "terminal_proof_verdict",
    "step_to_trit",
    "topology_provenance_errors",
    "verify_resolution_proof",
]


def terminal_proof_verdict(
    initial: dict[int, Clause], steps: list[ResolutionStep],
) -> bool:
    """Consume the entire certificate and disclose only its final validity.

    Continue checking declared clauses after a bad inference, accumulating failure.
    This deliberately non-localizing interface is not a last-clause-only check:
    the unchanged empty conclusion alone cannot detect a forged justification.
    """
    known = dict(initial)
    valid = True
    for step in steps:
        resolvent = None
        if step.left in known and step.right in known:
            resolvent = resolve_clause(known[step.left], known[step.right], step.pivot)
        local_ok = (
            step.sid not in known
            and resolvent is not None
            and resolvent == _canonical_clause(set(step.clause))
        )
        valid = local_ok and valid
        known[step.sid] = step.clause
    return bool(valid and steps and steps[-1].clause == ())


def run_strong_counterfeit(*, n: int = 24, forge_step_index: int = 3) -> dict[str, object]:
    """V3 scenario using the unchanged V2 adapter, with a downstream suffix.

    Ground truth and terminal verdicts are never inputs to the MCORE adapter.
    Hashes cover canonical JSON artifacts included in the receipt.
    """
    import hashlib
    import json
    from dataclasses import asdict

    if not 3 <= forge_step_index < n:
        raise ValueError("strong counterfeit requires a forge followed by descendants")
    clauses, intact = make_implication_chain(n)
    initial = {cid: clause for cid, clause in clauses.items() if cid <= n + 1}
    forged = forge_parent_reference(intact, step_index_1=forge_step_index)
    intact_ok, _ = verify_resolution_proof(initial, intact)
    forged_ok, first_bad = verify_resolution_proof(initial, forged)
    if not intact_ok or forged_ok or first_bad != forged[forge_step_index - 1].sid:
        raise ValueError("counterfeit ground-truth gate failed")

    # The detector receives only the frozen intact topology and observed syntax.
    control = topology_provenance_errors(intact, intact)
    errors = topology_provenance_errors(intact, forged)
    positions = [row["step_index"] for row in errors]
    artifacts = {
        "initial_clauses": initial,
        "intact_steps": [asdict(step) for step in intact],
        "forged_steps": [asdict(step) for step in forged],
    }
    hashes = {
        name: hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        for name, value in artifacts.items()
    }
    return {
        "benchmark": "MINT-GLACIER-847291 / V3 strong counterfeit",
        "adapter": "proof-edge-span-v2 (unchanged; intact topology required)",
        "claim_boundary": "Certificate-auditing benchmark only; not evidence about P vs NP",
        "comparison_boundary": "Non-localizing terminal interface; no runtime advantage claim",
        "proof_steps": n,
        "ground_truth": {"step_index": forge_step_index, "step_id": first_bad},
        "downstream_descendants": n - forge_step_index,
        "terminal_only": {
            "intact": terminal_proof_verdict(initial, intact),
            "forged": terminal_proof_verdict(initial, forged),
        },
        "mcore": {
            "intact_errors": control,
            "forged_errors": errors,
            "exact_localization": positions == [forge_step_index],
            "localization_distance": abs(positions[0] - forge_step_index) if positions else None,
        },
        "artifacts": artifacts,
        "sha256": hashes,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run_strong_counterfeit(), indent=2, sort_keys=True))
