"""Public-contract tests for the stable tree-validation API.

These tests use trees produced by the real builders.  A ``Constituent`` stores
its internal node label in ``.parent``; mocking a root with ``parent=None``
would describe an invalid object, not a root-edge case.
"""

from __future__ import annotations

import pytest

from mcore_1.check_tree import _expected_binary_depth, check_deletion, check_tree


@pytest.mark.parametrize(
    ("n", "expected"),
    [(0, 0), (1, 0), (2, 1), (3, 2), (4, 2), (5, 3)],
)
def test_expected_binary_depth(n: int, expected: int) -> None:
    assert _expected_binary_depth(n) == expected


def test_check_tree_rejects_invalid_weights() -> None:
    with pytest.raises(ValueError, match="each weight must be 0, 1, or 2"):
        check_tree([0, 1, 3, 2])


def test_check_tree_rejects_empty_weights() -> None:
    with pytest.raises(ValueError, match="weights must be non-empty"):
        check_tree([])


def test_check_tree_rejects_mismatched_depth() -> None:
    with pytest.raises(ValueError, match="depth 5 does not match"):
        check_tree([1, 2, 0, 1], depth=5)


def test_check_tree_returns_internal_rows_in_postorder_including_root() -> None:
    rows = check_tree([0, 0, 0, 0])

    assert [(row.leaf_lo, row.leaf_hi) for row in rows] == [(1, 2), (3, 4), (1, 4)]
    root = rows[-1]
    assert root.node_id
    assert not root.valid
    assert "OVERFLOW" in root.errors


def test_check_deletion_rejects_mismatched_lengths() -> None:
    with pytest.raises(ValueError, match="weights_mut must have length len"):
        check_deletion([1, 2, 1], [1], deletion_pos_1=2)


def test_check_deletion_rejects_out_of_bounds_index() -> None:
    with pytest.raises(ValueError, match="deletion_pos_1 must be in"):
        check_deletion([1, 2, 1], [1, 1], deletion_pos_1=5)


def test_check_deletion_rejects_single_column_wild_type() -> None:
    with pytest.raises(ValueError, match="cannot run deletion check on a single WT column"):
        check_deletion([1], [], deletion_pos_1=1)
