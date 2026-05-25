"""Tree validation: stable weight-stream API + ``mcore_py`` delegation."""

from __future__ import annotations

from dataclasses import dataclass

from mcore_py.checker import CheckError, CheckResult, check_tree as _check_tree_postorder
from mcore_py.model import Constituent, ProsodicUnit

from mcore_1.tree import (
    build_binary_metrical_tree,
    build_frozen_after_deletion_trits,
    descendant_orig_indices,
)


@dataclass(frozen=True)
class NodeResult:
    """Per-internal-node outcome from :func:`check_tree` / :func:`check_deletion`."""

    node_id: str
    leaf_lo: int
    leaf_hi: int
    valid: bool
    errors: list[str]


def check_constituent(root: Constituent) -> CheckResult:
    """Validate a :class:`~mcore_py.model.Constituent` root (full ``mcore_py`` rules)."""
    return _check_tree_postorder(root)


def check_tree(weights: list[int], *, depth: int | None = None) -> list[NodeResult]:
    """Post-order check on the bisection tree over leaf *weights* (0,1,2 = S1,S2,S3).

    Builds the same recursive bisection metrical tree as
    :func:`mcore_1.tree.build_binary_metrical_tree` with original indices
    ``1 .. len(weights)``.  Returns one :class:`NodeResult` per **internal**
    node in **post-order** (children before parent).

    If *depth* is given, it must equal ``ceil(log2(n))`` for ``n = len(weights)``
    (with ``ceil(log2(1)) := 0``), or :class:`ValueError` is raised.
    """
    if not weights:
        raise ValueError("weights must be non-empty")
    for w in weights:
        if w not in (0, 1, 2):
            raise ValueError(f"each weight must be 0, 1, or 2; got {w!r}")
    n = len(weights)
    d = _expected_binary_depth(n)
    if depth is not None and depth != d:
        raise ValueError(
            f"depth {depth} does not match ceil(log2({n})) == {d} for this length"
        )
    root = build_binary_metrical_tree(weights, list(range(1, n + 1)))
    if isinstance(root, ProsodicUnit):
        return []
    cr = _check_tree_postorder(root)
    return _collect_node_results_postorder(root, cr)


def check_deletion(
    weights_wt: list[int],
    weights_mut: list[int],
    deletion_pos_1: int,
) -> list[NodeResult]:
    """Compare WT vs mutant leaf weight streams after a single-column deletion at *k*.

    * *weights_wt*: wild-type leaf trits, length ``n`` (columns ``1..n``).
    * *weights_mut*: mutant leaf trits after deletion, length ``n - 1``.
    * *deletion_pos_1*: 1-based index ``k`` of the removed column in WT.

    Builds the mutant bisection tree with mutant leaf weights, freezes internal
    labels by re-pooling **WT** trits over the **mutant** topology (same rule as
    :func:`mcore_1.tree.build_post_deletion_frozen_tree`), then runs the standard
    checker.  Returns :class:`NodeResult` rows in **post-order** over internal nodes.
    """
    for name, seq in (("weights_wt", weights_wt), ("weights_mut", weights_mut)):
        for w in seq:
            if w not in (0, 1, 2):
                raise ValueError(f"{name} values must be 0, 1, or 2; got {w!r}")
    n = len(weights_wt)
    if len(weights_mut) != n - 1:
        raise ValueError(
            f"weights_mut must have length len(weights_wt)-1; got {len(weights_mut)} vs {n}"
        )
    if deletion_pos_1 < 1 or deletion_pos_1 > n:
        raise ValueError(f"deletion_pos_1 must be in [1, {n}]; got {deletion_pos_1}")
    if n == 1:
        raise ValueError("cannot run deletion check on a single WT column")
    root = build_frozen_after_deletion_trits(weights_wt, weights_mut, deletion_pos_1)
    assert isinstance(root, Constituent)
    cr = _check_tree_postorder(root)
    return _collect_node_results_postorder(root, cr)


def _expected_binary_depth(n: int) -> int:
    """``ceil(log2(n))`` with ``ceil(log2(1)) = 0`` (paper-style depth on leaves)."""
    if n <= 1:
        return 0
    return (n - 1).bit_length()


def _collect_node_results_postorder(root: Constituent, cr: CheckResult) -> list[NodeResult]:
    out: list[NodeResult] = []

    def walk(c: Constituent) -> None:
        for ch in c.children:
            if isinstance(ch, Constituent):
                walk(ch)
        S = descendant_orig_indices(c)
        lo, hi = S[0], S[-1]
        es = [e for e in cr.errors if e.node_id == c.parent.id]
        labels = [
            e.kind.name
            for e in es
            if e.kind.name in ("CONSERVATION", "OVERFLOW")
        ]
        out.append(
            NodeResult(
                node_id=c.parent.id,
                leaf_lo=lo,
                leaf_hi=hi,
                valid=len(es) == 0,
                errors=labels,
            )
        )

    walk(root)
    return out


__all__ = [
    "NodeResult",
    "check_tree",
    "check_deletion",
    "check_constituent",
    "CheckResult",
    "CheckError",
]
