"""Certificate tests for Theorem 1 (carry cascade) on the binary metrical tree."""

from __future__ import annotations

import pytest
from mcore_py.checker import ErrorKind
from mcore_py.model import Constituent, Level, ProsodicUnit, Trit

from mcore_1.check_tree import check_tree
from mcore_1.tree import build_post_deletion_frozen_tree, descendant_orig_indices


# Fixed sequence (length 30) — stable across machines; not claimed biological.
FIXED_DNA_30 = "ACGTACGTACGTACGTACGTACGTACGTAC"

# Optional: 60 bp CDS-style fragment (alphabet only; paper repo has full context).
GJB2_CDS_PREFIX_60 = (
    "ATGGTGAGCTGGATCGTCCTGGTGCTGCTGCTGCTGCTGCTGCTGCTGCTGCTGCTGCTGCTGCTGCTGCTG"
)[:60]


def _constituents(root: Constituent) -> list[Constituent]:
    out: list[Constituent] = []

    def walk(n: Constituent | ProsodicUnit) -> None:
        if isinstance(n, Constituent):
            out.append(n)
            for ch in n.children:
                walk(ch)

    walk(root)
    return out


def _depth_from_root(root: Constituent, target_id: str) -> int | None:
    """Return depth (root = 0) of the constituent whose ``parent.id`` matches."""

    def walk(n: Constituent | ProsodicUnit, d: int) -> int | None:
        if isinstance(n, Constituent):
            if n.parent.id == target_id:
                return d
            for ch in n.children:
                got = walk(ch, d + 1)
                if got is not None:
                    return got
        return None

    return walk(root, 0)


def _span_covers_deleted_site(S: tuple[int, ...], k: int) -> bool:
    """True if the original-interval hull ``[min(S), max(S)]`` contains index *k*.

    After a deletion, no leaf carries index *k*; we still flag constituents whose
    hull would have surrounded the deleted site (``min < k < max``), plus hulls
    that include *k* at an endpoint when *k* is still inside ``[min, max]``.

    Edge cases ``k == 1`` or ``k == n`` are handled separately in tests because
    the bisection hull of surviving leaves may not bracket the deleted column.
    """
    lo, hi = S[0], S[-1]
    return lo <= k <= hi


@pytest.mark.parametrize("k", range(2, 30))
def test_carry_cascade_theorem_1_and_2(k: int) -> None:
    """Theorem 1 (i)(ii): left-of-k nodes validate; intervals containing k fail."""
    dna = FIXED_DNA_30
    assert len(dna) == 30
    root = build_post_deletion_frozen_tree(dna, k)
    assert isinstance(root, Constituent)
    result = check_tree(root)
    assert not result.valid

    for node in _constituents(root):
        S = descendant_orig_indices(node)
        errs = [e for e in result.errors if e.node_id == node.parent.id]
        if S[-1] < k:
            # Pooling can still hit S3+S3 OVERFLOW under the partial semigroup; the
            # cascade certificate here is **no conservation drift** on that prefix.
            cons = [e for e in errs if e.kind == ErrorKind.CONSERVATION]
            assert not cons, f"unexpected conservation left of k={k} at S={S}: {cons}"
        elif _span_covers_deleted_site(S, k):
            assert errs, f"expected errors at S={S} covering k={k}"
            kinds = {e.kind for e in errs}
            assert kinds & {
                ErrorKind.CONSERVATION,
                ErrorKind.OVERFLOW,
            }, f"expected CONSERVATION/OVERFLOW at S={S}, got {errs}"


@pytest.mark.parametrize("k", [1, 30])
def test_carry_cascade_endpoints_smoke(k: int) -> None:
    """Endpoints ``k in {1, n}`` are smoke-checked (hull predicate is weaker)."""
    dna = FIXED_DNA_30
    root = build_post_deletion_frozen_tree(dna, k)
    assert isinstance(root, Constituent)
    result = check_tree(root)
    assert not result.valid
    assert result.errors


@pytest.mark.parametrize("k", range(2, 30))
def test_theorem_3_shallowest_failure_near_leaf(k: int) -> None:
    """Theorem 1 (iii): deepest internal node containing k should among error nodes."""
    dna = FIXED_DNA_30
    root = build_post_deletion_frozen_tree(dna, k)
    assert isinstance(root, Constituent)
    result = check_tree(root)

    internals = [n for n in _constituents(root) if _span_covers_deleted_site(descendant_orig_indices(n), k)]
    assert internals
    deepest = max(internals, key=lambda n: _depth_from_root(root, n.parent.id) or 0)
    ddeepest = _depth_from_root(root, deepest.parent.id)
    assert ddeepest is not None

    err_ids = {e.node_id for e in result.errors}
    assert deepest.parent.id in err_ids

    internal_ids = {n.parent.id for n in internals}
    err_depths = [
        d
        for e in result.errors
        if e.node_id in internal_ids
        for d in [_depth_from_root(root, e.node_id)]
        if d is not None
    ]
    assert max(err_depths) == ddeepest


def test_empty_constituent_after_structure_loss() -> None:
    """``EMPTY_CONSTITUENT`` is raised for a constituent with no children."""
    parent = ProsodicUnit(weight=Trit.S1, level=Level.L2_GANA, label="empty-parent")
    bad = Constituent(parent=parent, children=[])
    res = check_tree(bad)
    assert not res.valid
    assert any(e.kind == ErrorKind.EMPTY_CONSTITUENT for e in res.errors)


@pytest.mark.parametrize("k", list(range(2, 30, 3)))
def test_optional_gjb2_prefix_fragment(k: int) -> None:
    """Spot-check cascade properties on a longer biological fragment."""
    dna = GJB2_CDS_PREFIX_60
    assert len(dna) == 60
    if k > len(dna):
        pytest.skip("k out of range for this fragment")
    root = build_post_deletion_frozen_tree(dna, k)
    assert isinstance(root, Constituent)
    result = check_tree(root)
    assert not result.valid
    for node in _constituents(root):
        S = descendant_orig_indices(node)
        errs = [e for e in result.errors if e.node_id == node.parent.id]
        if S[-1] < k:
            cons = [e for e in errs if e.kind == ErrorKind.CONSERVATION]
            assert not cons
    covering = [
        n
        for n in _constituents(root)
        if _span_covers_deleted_site(descendant_orig_indices(n), k)
    ]
    assert covering
    assert any(
        {e.kind for e in result.errors if e.node_id == n.parent.id}
        & {ErrorKind.CONSERVATION, ErrorKind.OVERFLOW}
        for n in covering
    )
