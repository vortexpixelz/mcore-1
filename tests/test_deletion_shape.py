"""Tests for the generic deletion-shape API (mcore_1.deletion_shape).

Covers determinism/UUID-independence, deterministic reorder normalization,
two-signature roles, coordinate semantics, null handling, tie handling, and
malformed-input rejection.
"""

from __future__ import annotations

import json
import random

import pytest

from mcore_1.check_tree import NodeResult, check_deletion
from mcore_1.deletion_shape import (
    SCHEMA_VERSION,
    _reconstruct_postorder,
    summarize_deletion_shape,
)
from mcore_1.encoder import dna_to_trits

FIXED_DNA_30 = "ACGTACGTACGTACGTACGTACGTACGTAC"


def _rows_for(dna: str, k: int):
    wt, _ = dna_to_trits(dna)
    mut, _ = dna_to_trits(dna[: k - 1] + dna[k:])
    return check_deletion(wt, mut, k), len(wt), len(mut)


def _rows_over_topology(n: int, k: int, valid_of, errors_of=None):
    """Synthetic NodeResult rows over the real (n, k) topology spans."""
    rows = []
    for lo, hi, _s in _reconstruct_postorder(n, n - 1, k):
        valid = valid_of(lo, hi)
        errs = [] if valid else (errors_of(lo, hi) if errors_of else ["CONSERVATION"])
        rows.append(NodeResult(f"uuid-{lo}-{hi}", lo, hi, valid, errs))
    return rows


# ---------------------------------------------------------------------------
# Determinism / UUID independence
# ---------------------------------------------------------------------------


def test_determinism_across_repeated_and_fresh_calls() -> None:
    dna, k = FIXED_DNA_30, 12
    rows1, n, m = _rows_for(dna, k)
    s1 = summarize_deletion_shape(rows1, deletion_pos_1=k, wt_length=n, mutant_length=m)
    s1b = summarize_deletion_shape(rows1, deletion_pos_1=k, wt_length=n, mutant_length=m)

    rows2, _, _ = _rows_for(dna, k)  # fresh check_deletion → new random node UUIDs
    assert {r.node_id for r in rows1} != {r.node_id for r in rows2}
    s2 = summarize_deletion_shape(rows2, deletion_pos_1=k, wt_length=n, mutant_length=m)

    assert s1.to_canonical_json() == s1b.to_canonical_json() == s2.to_canonical_json()
    assert s1.receipt_signature() == s2.receipt_signature()
    assert s1.geometry_signature() == s2.geometry_signature()
    assert s1.schema_version == SCHEMA_VERSION


def test_two_signatures_distinct_roles() -> None:
    rows, n, m = _rows_for(FIXED_DNA_30, 12)
    s = summarize_deletion_shape(rows, deletion_pos_1=12, wt_length=n, mutant_length=m)
    assert len(s.receipt_signature()) == 64
    assert len(s.geometry_signature()) == 64
    # Different payloads (absolute vs k-relative) → different digests.
    assert s.receipt_signature() != s.geometry_signature()
    # Canonical JSON excludes any UUID substring.
    assert "uuid" not in s.to_canonical_json().lower()


# ---------------------------------------------------------------------------
# Reorder normalization + malformed rejection
# ---------------------------------------------------------------------------


def test_reorder_is_normalized_deterministically() -> None:
    rows, n, m = _rows_for(FIXED_DNA_30, 7)
    base = summarize_deletion_shape(rows, deletion_pos_1=7, wt_length=n, mutant_length=m)
    shuffled = rows[:]
    random.Random(0).shuffle(shuffled)
    s = summarize_deletion_shape(shuffled, deletion_pos_1=7, wt_length=n, mutant_length=m)
    assert s.to_canonical_json() == base.to_canonical_json()
    assert s.receipt_signature() == base.receipt_signature()
    assert s.geometry_signature() == base.geometry_signature()


def test_duplicate_span_rejected() -> None:
    rows, n, m = _rows_for(FIXED_DNA_30, 7)
    with pytest.raises(ValueError, match="duplicate span"):
        summarize_deletion_shape(
            rows + [rows[0]], deletion_pos_1=7, wt_length=n, mutant_length=m
        )


def test_span_set_mismatch_rejected() -> None:
    rows, n, m = _rows_for(FIXED_DNA_30, 7)
    bad = rows[:-1] + [NodeResult("x", 999, 1000, False, ["OVERFLOW"])]
    with pytest.raises(ValueError, match="does not match mutant topology"):
        summarize_deletion_shape(bad, deletion_pos_1=7, wt_length=n, mutant_length=m)


def test_valid_row_with_error_labels_rejected() -> None:
    rows = _rows_over_topology(16, 8, valid_of=lambda lo, hi: True)
    rows[0] = NodeResult(rows[0].node_id, rows[0].leaf_lo, rows[0].leaf_hi, True, ["CONSERVATION"])
    with pytest.raises(ValueError, match="valid row carries error labels"):
        summarize_deletion_shape(rows, deletion_pos_1=8, wt_length=16, mutant_length=15)


def test_degenerate_span_rejected() -> None:
    rows = [NodeResult("a", 5, 3, False, ["OVERFLOW"])]
    with pytest.raises(ValueError, match="degenerate span"):
        summarize_deletion_shape(rows, deletion_pos_1=2, wt_length=4, mutant_length=3)


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(deletion_pos_1=1, wt_length=1, mutant_length=0),  # wt too short
        dict(deletion_pos_1=1, wt_length=6, mutant_length=4),  # mutant_length wrong
        dict(deletion_pos_1=9, wt_length=6, mutant_length=5),  # k out of range
    ],
)
def test_kwarg_validation(kwargs) -> None:
    with pytest.raises(ValueError):
        summarize_deletion_shape([], **kwargs)


# ---------------------------------------------------------------------------
# Coordinate semantics + classification
# ---------------------------------------------------------------------------


def test_site_classification_and_width_vs_survivors() -> None:
    n, k = 16, 8
    rows = _rows_over_topology(n, k, valid_of=lambda lo, hi: False)
    s = summarize_deletion_shape(rows, deletion_pos_1=k, wt_length=n, mutant_length=n - 1)

    assert (
        s.invalid_left_of_deletion_count
        + s.invalid_contains_deletion_count
        + s.invalid_right_of_deletion_count
        == s.invalid_node_count
    )
    for node in s.invalid_nodes:
        if node.leaf_hi < k:
            assert node.site_class == "left"
        elif node.leaf_lo > k:
            assert node.site_class == "right"
        else:
            assert node.site_class == "contains"
        assert node.coordinate_width == node.leaf_hi - node.leaf_lo + 1
        assert node.coordinate_width >= node.survivor_leaf_count
    # A hull that straddles the (removed) site k has width > survivors by exactly 1.
    straddlers = [nd for nd in s.invalid_nodes if nd.site_class == "contains"]
    assert straddlers
    assert any(nd.coordinate_width == nd.survivor_leaf_count + 1 for nd in straddlers)


# ---------------------------------------------------------------------------
# Null handling / mixed errors / ties
# ---------------------------------------------------------------------------


def test_all_valid_tree_has_null_spans() -> None:
    n, k = 8, 4
    rows = _rows_over_topology(n, k, valid_of=lambda lo, hi: True)
    s = summarize_deletion_shape(rows, deletion_pos_1=k, wt_length=n, mutant_length=n - 1)
    assert s.invalid_node_count == 0
    assert s.first_invalid_span is None
    assert s.narrowest_invalid_span is None
    assert s.widest_invalid_span is None
    assert s.error_kind_counts == {"CONSERVATION": 0, "OVERFLOW": 0}
    d = json.loads(s.to_canonical_json())
    assert d["first_invalid_span"] is None
    assert json.loads(s.geometry_canonical_json())["first_invalid_relative"] is None


def test_mixed_error_counts_and_serialization() -> None:
    n, k = 8, 4
    topo = _reconstruct_postorder(n, n - 1, k)
    rows = []
    for i, (lo, hi, _s) in enumerate(topo):
        if i == 0:
            rows.append(NodeResult("a", lo, hi, False, ["OVERFLOW"]))
        elif i == 1:
            rows.append(NodeResult("b", lo, hi, False, []))  # invalid, unlabeled
        else:
            rows.append(NodeResult(f"v{lo}-{hi}", lo, hi, True, []))
    s = summarize_deletion_shape(rows, deletion_pos_1=k, wt_length=n, mutant_length=n - 1)
    assert s.error_kind_counts["OVERFLOW"] == 1
    assert s.invalid_without_listed_kind_count == 1
    assert s.invalid_node_count == 2
    json.loads(s.to_canonical_json())  # serializes


def test_narrowest_widest_deterministic_ties() -> None:
    n, k = 16, 8
    rows = _rows_over_topology(n, k, valid_of=lambda lo, hi: False)
    s = summarize_deletion_shape(rows, deletion_pos_1=k, wt_length=n, mutant_length=n - 1)
    widths = [nd.coordinate_width for nd in s.invalid_nodes]
    minw, maxw = min(widths), max(widths)
    narrow_ties = [(nd.leaf_lo, nd.leaf_hi) for nd in s.invalid_nodes if nd.coordinate_width == minw]
    wide_ties = [(nd.leaf_lo, nd.leaf_hi) for nd in s.invalid_nodes if nd.coordinate_width == maxw]
    assert s.narrowest_invalid_span == min(narrow_ties)
    assert s.widest_invalid_span == min(wide_ties)  # documented rule: smallest (lo,hi)

    shuffled = rows[:]
    random.Random(3).shuffle(shuffled)
    s2 = summarize_deletion_shape(shuffled, deletion_pos_1=k, wt_length=n, mutant_length=n - 1)
    assert (s2.narrowest_invalid_span, s2.widest_invalid_span) == (
        s.narrowest_invalid_span,
        s.widest_invalid_span,
    )


# ---------------------------------------------------------------------------
# Edge topology + check_deletion unchanged
# ---------------------------------------------------------------------------


def test_singleton_mutant_topology() -> None:
    wt, k = [0, 1], 1
    mut = [1]  # delete column 1
    rows = check_deletion(wt, mut, k)
    s = summarize_deletion_shape(rows, deletion_pos_1=k, wt_length=2, mutant_length=1)
    assert s.total_internal_nodes == len(rows) == 1
    json.loads(s.to_canonical_json())


def test_check_deletion_behavior_unchanged() -> None:
    rows, n, m = _rows_for(FIXED_DNA_30, 12)
    assert (n, m) == (30, 29)
    assert len(rows) >= 1
    assert any(not r.valid for r in rows)
    s = summarize_deletion_shape(rows, deletion_pos_1=12, wt_length=n, mutant_length=m)
    assert s.total_internal_nodes == len(rows)
    assert s.valid_node_count + s.invalid_node_count == len(rows)
    assert s.invalid_node_count == sum(1 for r in rows if not r.valid)
