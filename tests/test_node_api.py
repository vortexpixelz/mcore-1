"""Stable weight-stream ``check_tree`` / ``check_deletion`` API."""

from __future__ import annotations

import pytest

from mcore_1.check_tree import check_constituent, check_deletion, check_tree
from mcore_1.encoder import dna_to_trits
from mcore_1.tree import build_binary_metrical_tree, build_post_deletion_frozen_tree


def test_check_tree_all_valid_on_balanced_leaves() -> None:
    # Two leaves: S1 + S2 = S3 (no overflow)
    w = [0, 1]
    rows = check_tree(w, depth=1)
    assert len(rows) == 1
    assert all(r.valid for r in rows)
    assert rows[0].leaf_lo == 1 and rows[0].leaf_hi == 2


def test_check_tree_four_leaves_may_have_overflow() -> None:
    """Four S1 leaves pool to overflow at the root under bisection; rows report it."""
    w = [0, 0, 0, 0]
    rows = check_tree(w, depth=2)
    assert len(rows) == 3
    assert not rows[-1].valid  # root pools two S2 children → overflow


def test_check_tree_single_leaf_returns_empty() -> None:
    assert check_tree([1]) == []


def test_check_tree_depth_mismatch_raises() -> None:
    with pytest.raises(ValueError, match="depth"):
        check_tree([0, 0, 0, 0], depth=99)


def test_check_deletion_matches_dna_built_tree() -> None:
    dna = "ACGTACGTACGTACGTACGTACGTACGTAC"
    k = 12
    wt, _ = dna_to_trits(dna)
    mut, _ = dna_to_trits(dna[: k - 1] + dna[k:])
    from_rows = check_deletion(wt, mut, k)
    root = build_post_deletion_frozen_tree(dna, k)
    from_const = check_constituent(root)
    assert not from_const.valid
    assert sum(1 for r in from_rows if not r.valid) >= 1
    assert len(from_rows) >= 1


def test_check_constituent_roundtrip() -> None:
    root = build_binary_metrical_tree([0, 1], [1, 2])
    res = check_constituent(root)
    assert res.valid
