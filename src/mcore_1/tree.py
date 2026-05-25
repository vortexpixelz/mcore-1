"""Binary metrical tree construction over MCORE-1 trit leaves.

A length-``n`` sequence is arranged as a **recursive bisection** binary tree:
split the current list into ``left = s[:mid]``, ``right = s[mid:]`` with
``mid = len(s) // 2`` (so ``len(left) <= len(right)`` and ``len(left) >= 1``).

Internal node weights use ``mcore_py`` trit addition (S1/S2/S3 with overflow).

**Frozen certificates** after a deletion: each internal node's declared weight
is the **balanced pool** of **pre-deletion** trits at the same original columns,
using the **post-deletion** tree topology (same parent/child shape as the
checker will evaluate).  Leaves keep **post-deletion** re-encoded weights.  Any
node whose descendant set lies entirely **left** of the deleted index therefore
matches the pre-deletion subtree and validates; nodes whose original index
range straddles the deletion site typically fail CONSERVATION / OVERFLOW.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcore_py.algebra import OVERFLOW, trit_add
from mcore_py.model import Constituent, Level, ProsodicUnit, Trit

from mcore_1.encoder import dna_to_trits

if TYPE_CHECKING:
    pass

_SPAN_KEY = "orig_span"  # (lo, hi) = (min(S), max(S)) of descendant original indices


_LEVEL_ORDER: tuple[Level, ...] = (
    Level.L0_MATRA,
    Level.L1_AKSARA,
    Level.L2_GANA,
    Level.L3_PADA,
    Level.L4_SLOKA,
)


def _level_for_depth(depth_from_leaves: int) -> Level:
    idx = min(max(depth_from_leaves, 0), len(_LEVEL_ORDER) - 1)
    return _LEVEL_ORDER[idx]


def _node_weight(node: ProsodicUnit | Constituent) -> Trit:
    if isinstance(node, Constituent):
        return node.parent.weight
    return node.weight


def build_binary_metrical_tree(
    trits: list[int],
    orig_indices: list[int],
) -> ProsodicUnit | Constituent:
    """Build a binary metrical tree over parallel *trits* / *orig_indices*.

    Each leaf stores ``features[orig_span] = (i, i)``.  Internal nodes store
    ``(min(S), max(S))`` where ``S`` is the set of descendant original indices.
    """
    if len(trits) != len(orig_indices):
        raise ValueError("trits and orig_indices must have the same length")
    if len(trits) == 0:
        raise ValueError("cannot build an empty tree")
    return _build_range(trits, orig_indices, depth_from_leaves=0)


def _build_range(
    trits: list[int],
    orig: list[int],
    *,
    depth_from_leaves: int,
) -> ProsodicUnit | Constituent:
    n = len(trits)
    if n == 1:
        lo = hi = orig[0]
        pu = ProsodicUnit(
            weight=Trit(trits[0]),
            level=Level.L0_MATRA,
            label=f"leaf:{lo}",
        )
        pu.features[_SPAN_KEY] = (lo, hi)
        return pu

    mid = n // 2
    left_t, right_t = trits[:mid], trits[mid:]
    left_o, right_o = orig[:mid], orig[mid:]
    left_child = _build_range(left_t, left_o, depth_from_leaves=depth_from_leaves + 1)
    right_child = _build_range(right_t, right_o, depth_from_leaves=depth_from_leaves + 1)

    wl = _node_weight(left_child)
    wr = _node_weight(right_child)
    pooled = trit_add(wl, wr)
    if pooled is OVERFLOW:
        pw = Trit.S3
    else:
        pw = pooled

    idxs = sorted(_descendant_orig_indices_tuple(left_child) + _descendant_orig_indices_tuple(right_child))
    lo, hi = idxs[0], idxs[-1]
    parent = ProsodicUnit(
        weight=pw,
        level=_level_for_depth(depth_from_leaves + 1),
        label=f"node:{lo}-{hi}",
    )
    parent.features[_SPAN_KEY] = (lo, hi)
    parent.features["orig_indices"] = tuple(idxs)
    const = Constituent(parent=parent, children=[left_child, right_child])
    return const


def _descendant_orig_indices_tuple(node: ProsodicUnit | Constituent) -> list[int]:
    if isinstance(node, ProsodicUnit):
        lo, hi = orig_span(node)
        assert lo == hi
        return [lo]
    t = node.parent.features.get("orig_indices")
    if isinstance(t, tuple):
        return list(t)
    return sorted(
        x for ch in node.children for x in _descendant_orig_indices_tuple(ch)
    )


def descendant_orig_indices(node: ProsodicUnit | Constituent) -> tuple[int, ...]:
    """Sorted original 1-based indices of all leaves under *node*."""
    return tuple(_descendant_orig_indices_tuple(node))


def orig_span(node: ProsodicUnit | Constituent) -> tuple[int, int]:
    """Return ``(min(S), max(S))`` for descendant original indices (inclusive)."""
    if isinstance(node, Constituent):
        span = node.parent.features.get(_SPAN_KEY)
    else:
        span = node.features.get(_SPAN_KEY)
    if not span:
        raise ValueError("node missing orig_span feature")
    return int(span[0]), int(span[1])


def frozen_weight_for_interval(orig_trits: list[int], lo: int, hi: int) -> Trit:
    """Balanced-tree pooled weight for a **contiguous** original slice ``[lo, hi]``.

    Uses :func:`build_binary_metrical_tree` on that slice alone (diagnostics).
    """
    if lo > hi:
        raise ValueError("empty interval")
    sub_t = orig_trits[lo - 1 : hi]
    sub_o = list(range(lo, hi + 1))
    root = build_binary_metrical_tree(sub_t, sub_o)
    w = _node_weight(root)
    assert isinstance(w, Trit)
    return w


def pool_original_trits_for_interval(
    orig_trits: list[int],
    lo: int,
    hi: int,
) -> Trit:
    """Alias for :func:`frozen_weight_for_interval`."""
    return frozen_weight_for_interval(orig_trits, lo, hi)


def _pooled_orig_trits_on_topology(
    node: ProsodicUnit | Constituent,
    orig_trits: list[int],
) -> Trit:
    """Post-order: pool *orig_trits* at descendant columns using *node*'s shape."""
    if isinstance(node, ProsodicUnit):
        lo, hi = orig_span(node)
        assert lo == hi
        return Trit(orig_trits[lo - 1])
    assert isinstance(node, Constituent)
    if len(node.children) == 1:
        w0 = _pooled_orig_trits_on_topology(node.children[0], orig_trits)
        node.parent.weight = w0
        return w0
    assert len(node.children) == 2
    w0 = _pooled_orig_trits_on_topology(node.children[0], orig_trits)
    w1 = _pooled_orig_trits_on_topology(node.children[1], orig_trits)
    pooled = trit_add(w0, w1)
    pw = Trit.S3 if pooled is OVERFLOW else pooled
    node.parent.weight = pw
    return pw


def build_post_deletion_frozen_tree(
    dna: str,
    k: int,
    *,
    orig_trits: list[int] | None = None,
) -> Constituent | ProsodicUnit:
    """Tree after deleting 1-based position *k*, with **frozen** internal weights.

    Internal labels re-pool **pre-deletion** trits at each leaf column using the
    **post-deletion** bisection topology (see module docstring).  Leaves use the
    **post-deletion** re-encoded trits.
    """
    if k < 1 or k > len(dna):
        raise ValueError(f"k must be in [1, len(dna)]; got k={k}, len={len(dna)}")
    if orig_trits is None:
        orig_trits, _ = dna_to_trits(dna)

    new_dna = dna[: k - 1] + dna[k:]
    if not new_dna:
        raise ValueError("deleting the only base yields an empty sequence (no tree)")
    new_trits, _ = dna_to_trits(new_dna)
    new_orig = [i for i in range(1, len(dna) + 1) if i != k]

    root = build_binary_metrical_tree(new_trits, new_orig)
    if isinstance(root, ProsodicUnit):
        root = _wrap_singleton_leaf(root)
    assert isinstance(root, Constituent)
    _pooled_orig_trits_on_topology(root, orig_trits)
    return root


def _wrap_singleton_leaf(leaf: ProsodicUnit) -> Constituent:
    lo, hi = orig_span(leaf)
    parent = ProsodicUnit(
        weight=leaf.weight,
        level=Level.L1_AKSARA,
        label=f"wrap:{lo}-{hi}",
    )
    parent.features[_SPAN_KEY] = (lo, hi)
    parent.features["orig_indices"] = (lo,)
    return Constituent(parent=parent, children=[leaf])
