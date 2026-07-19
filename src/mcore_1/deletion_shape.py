"""Generic, deterministic deletion-shape summary + signatures for MCORE-1.

Source-of-record for turning :func:`mcore_1.check_tree.check_deletion`
:class:`~mcore_1.check_tree.NodeResult` rows into a canonical, hash-stable
geometry record.

Two independent SHA-256 signatures are produced:

* ``receipt_signature`` — over the **complete absolute** canonical artifact
  (absolute original-coordinate spans, the deletion site ``k``, all counts).
  This is the identity of the full receipt for a specific deletion.
* ``geometry_signature`` — over the **normalized structural geometry expressed
  relative to** the deletion site ``k`` (offsets ``lo - k`` / ``hi - k``,
  widths, survivor counts, error kinds, left/contains/right class). Absolute
  position is stripped, so two deletions with the same *relative* error
  geometry share a ``geometry_signature`` even at different sites.

Compare ``geometry_signature`` (never ``receipt_signature``) to test whether two
deletions produce the same error geometry.

**Determinism guarantee.** Node identity in both signatures is the deterministic
span ``(leaf_lo, leaf_hi)`` and post-order rank — never the runtime
``ProsodicUnit.id`` (a random ``uuid.uuid4()`` regenerated on every
``check_deletion`` call). That is what makes the canonical JSON and both
signatures byte-identical across repeated calls.

**Reordering behavior (documented, chosen: normalized deterministically).**
The output depends only on the *set* of node records plus
``(deletion_pos_1, wt_length, mutant_length)``, not on input row order. The
authoritative post-order is reconstructed from the mutant bisection topology
(via :func:`mcore_1.tree.build_frozen_after_deletion_trits` with placeholder
weights), and input rows are matched to it by span. Duplicate spans, spans that
do not match the reconstructed topology, ``valid``/``errors`` inconsistencies,
and degenerate spans all raise :class:`ValueError`.

**Coordinate semantics.** Spans are in **original 1-based** coordinates; after a
deletion the surviving leaves keep their original indices (the deleted index
``k`` is absent). For a node with hull ``[lo, hi]``:

* ``coordinate_width = hi - lo + 1`` — width of the original-coordinate hull,
  which *may include the deleted site* ``k``.
* ``survivor_leaf_count`` — number of surviving original indices actually under
  the node (never counts ``k``). These differ exactly when the hull straddles
  ``k``.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from mcore_1.check_tree import NodeResult
from mcore_1.tree import build_frozen_after_deletion_trits, descendant_orig_indices

SCHEMA_VERSION = "mcore1.deletion_shape/1"

# Error kinds that :class:`NodeResult` surfaces into ``errors`` (see check_tree).
_LISTED_ERROR_KINDS: tuple[str, ...] = ("CONSERVATION", "OVERFLOW")

Span = tuple[int, int]


@dataclass(frozen=True)
class NodeRecord:
    """One internal node in a deletion tree (deterministic, UUID-free)."""

    post_rank: int  # 0-based post-order rank in the mutant topology
    node_id: str  # deterministic "{post_rank}:{leaf_lo}-{leaf_hi}" (never a UUID)
    leaf_lo: int  # original 1-based hull minimum
    leaf_hi: int  # original 1-based hull maximum
    coordinate_width: int  # leaf_hi - leaf_lo + 1 (may include deleted site k)
    survivor_leaf_count: int  # surviving original indices under the node (excludes k)
    valid: bool
    site_class: str  # "left" | "contains" | "right" relative to k
    error_kinds: tuple[str, ...]  # sorted; subset of _LISTED_ERROR_KINDS

    def to_dict(self) -> dict[str, Any]:
        return {
            "post_rank": self.post_rank,
            "node_id": self.node_id,
            "leaf_lo": self.leaf_lo,
            "leaf_hi": self.leaf_hi,
            "coordinate_width": self.coordinate_width,
            "survivor_leaf_count": self.survivor_leaf_count,
            "valid": self.valid,
            "site_class": self.site_class,
            "error_kinds": list(self.error_kinds),
        }


@dataclass(frozen=True)
class DeletionShape:
    """Canonical, hash-stable summary of a single deletion's validator geometry."""

    schema_version: str
    deletion_pos_1: int
    wt_length: int
    mutant_length: int
    total_internal_nodes: int
    valid_node_count: int
    invalid_node_count: int
    invalid_without_listed_kind_count: int
    error_kind_counts: dict[str, int]
    invalid_nodes: tuple[NodeRecord, ...]
    first_invalid_span: Span | None  # first invalid node in post-order
    narrowest_invalid_span: Span | None  # min coordinate_width, tie by (lo, hi)
    widest_invalid_span: Span | None  # max coordinate_width, tie by (lo, hi)
    invalid_contains_deletion_count: int
    invalid_left_of_deletion_count: int
    invalid_right_of_deletion_count: int

    # -- canonical serializations -------------------------------------------

    def to_receipt_dict(self) -> dict[str, Any]:
        """Complete absolute canonical payload (basis of ``receipt_signature``)."""
        return {
            "schema_version": self.schema_version,
            "deletion_pos_1": self.deletion_pos_1,
            "wt_length": self.wt_length,
            "mutant_length": self.mutant_length,
            "total_internal_nodes": self.total_internal_nodes,
            "valid_node_count": self.valid_node_count,
            "invalid_node_count": self.invalid_node_count,
            "invalid_without_listed_kind_count": self.invalid_without_listed_kind_count,
            "error_kind_counts": dict(self.error_kind_counts),
            "invalid_nodes": [n.to_dict() for n in self.invalid_nodes],
            "first_invalid_span": _span_to_list(self.first_invalid_span),
            "narrowest_invalid_span": _span_to_list(self.narrowest_invalid_span),
            "widest_invalid_span": _span_to_list(self.widest_invalid_span),
            "invalid_contains_deletion_count": self.invalid_contains_deletion_count,
            "invalid_left_of_deletion_count": self.invalid_left_of_deletion_count,
            "invalid_right_of_deletion_count": self.invalid_right_of_deletion_count,
        }

    def to_geometry_dict(self) -> dict[str, Any]:
        """Normalized geometry relative to ``k`` (basis of ``geometry_signature``).

        Absolute position (``deletion_pos_1`` and absolute ``lo``/``hi``) is
        removed; spans become offsets ``lo - k`` / ``hi - k``. Sizes and relative
        structure are retained, so two deletions with matching relative geometry
        produce identical ``geometry_signature`` values.
        """
        k = self.deletion_pos_1
        return {
            "schema_version": self.schema_version,
            "wt_length": self.wt_length,
            "mutant_length": self.mutant_length,
            "total_internal_nodes": self.total_internal_nodes,
            "valid_node_count": self.valid_node_count,
            "invalid_node_count": self.invalid_node_count,
            "invalid_without_listed_kind_count": self.invalid_without_listed_kind_count,
            "error_kind_counts": dict(self.error_kind_counts),
            "invalid_nodes_relative": [
                {
                    "post_rank": n.post_rank,
                    "lo_offset": n.leaf_lo - k,
                    "hi_offset": n.leaf_hi - k,
                    "coordinate_width": n.coordinate_width,
                    "survivor_leaf_count": n.survivor_leaf_count,
                    "site_class": n.site_class,
                    "error_kinds": list(n.error_kinds),
                }
                for n in self.invalid_nodes
            ],
            "first_invalid_relative": _rel_span(self.first_invalid_span, k),
            "narrowest_invalid_relative": _rel_span(self.narrowest_invalid_span, k),
            "widest_invalid_relative": _rel_span(self.widest_invalid_span, k),
            "invalid_contains_deletion_count": self.invalid_contains_deletion_count,
            "invalid_left_of_deletion_count": self.invalid_left_of_deletion_count,
            "invalid_right_of_deletion_count": self.invalid_right_of_deletion_count,
        }

    def to_canonical_json(self) -> str:
        """Byte-stable canonical JSON of the full receipt payload."""
        return _canonical_json(self.to_receipt_dict())

    def geometry_canonical_json(self) -> str:
        """Byte-stable canonical JSON of the normalized geometry payload."""
        return _canonical_json(self.to_geometry_dict())

    def receipt_signature(self) -> str:
        """SHA-256 over the complete absolute canonical artifact."""
        return hashlib.sha256(self.to_canonical_json().encode("utf-8")).hexdigest()

    def geometry_signature(self) -> str:
        """SHA-256 over the normalized geometry (relative to ``k``)."""
        return hashlib.sha256(
            self.geometry_canonical_json().encode("utf-8")
        ).hexdigest()


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def node_records(
    rows: list[NodeResult],
    *,
    deletion_pos_1: int,
    wt_length: int,
    mutant_length: int,
) -> list[NodeRecord]:
    """All internal nodes (valid + invalid) in authoritative post-order.

    Validates the row set against the reconstructed mutant topology and pairs by
    span. See module docstring for reorder / coordinate semantics. Raises
    :class:`ValueError` on inconsistent lengths, out-of-range ``k``,
    duplicate/malformed spans, or a ``valid``/``errors`` inconsistency.
    """
    n = wt_length
    if n < 2:
        raise ValueError(f"wt_length must be >= 2; got {n}")
    if mutant_length != n - 1:
        raise ValueError(
            f"mutant_length must equal wt_length - 1; got {mutant_length} vs {n}"
        )
    if not (1 <= deletion_pos_1 <= n):
        raise ValueError(f"deletion_pos_1 must be in [1, {n}]; got {deletion_pos_1}")
    k = deletion_pos_1

    by_span: dict[Span, NodeResult] = {}
    for r in rows:
        if r.leaf_lo > r.leaf_hi:
            raise ValueError(f"degenerate span lo>hi: ({r.leaf_lo}, {r.leaf_hi})")
        labels = tuple(r.errors)
        for lab in labels:
            if lab not in _LISTED_ERROR_KINDS:
                raise ValueError(f"unexpected error kind {lab!r} in row {r.node_id}")
        if r.valid and labels:
            raise ValueError(
                f"valid row carries error labels {labels!r} (node {r.node_id})"
            )
        span = (r.leaf_lo, r.leaf_hi)
        if span in by_span:
            raise ValueError(f"duplicate span in rows: {span}")
        by_span[span] = r

    topo = _reconstruct_postorder(n, mutant_length, k)  # list[(lo, hi, survivors)]
    topo_spans = {(lo, hi) for (lo, hi, _s) in topo}
    if topo_spans != set(by_span):
        missing = topo_spans - set(by_span)
        extra = set(by_span) - topo_spans
        raise ValueError(
            "row span set does not match mutant topology; "
            f"missing={sorted(missing)} extra={sorted(extra)}"
        )

    out: list[NodeRecord] = []
    for rank, (lo, hi, survivors) in enumerate(topo):
        row = by_span[(lo, hi)]
        kinds = tuple(sorted(row.errors))
        out.append(
            NodeRecord(
                post_rank=rank,
                node_id=f"{rank}:{lo}-{hi}",
                leaf_lo=lo,
                leaf_hi=hi,
                coordinate_width=hi - lo + 1,
                survivor_leaf_count=survivors,
                valid=row.valid,
                site_class=_classify_site(lo, hi, k),
                error_kinds=kinds,
            )
        )
    return out


def summarize_deletion_shape(
    rows: list[NodeResult],
    *,
    deletion_pos_1: int,
    wt_length: int,
    mutant_length: int,
) -> DeletionShape:
    """Summarize ``check_deletion`` *rows* into a canonical :class:`DeletionShape`."""
    records = node_records(
        rows,
        deletion_pos_1=deletion_pos_1,
        wt_length=wt_length,
        mutant_length=mutant_length,
    )
    k = deletion_pos_1
    invalid = [r for r in records if not r.valid]

    kind_counts: dict[str, int] = {kind: 0 for kind in _LISTED_ERROR_KINDS}
    invalid_unlabeled = 0
    contains_ct = left_ct = right_ct = 0
    for r in invalid:
        if not r.error_kinds:
            invalid_unlabeled += 1
        for kind in r.error_kinds:
            kind_counts[kind] += 1
        if r.site_class == "contains":
            contains_ct += 1
        elif r.site_class == "left":
            left_ct += 1
        else:
            right_ct += 1

    first_invalid = (invalid[0].leaf_lo, invalid[0].leaf_hi) if invalid else None

    return DeletionShape(
        schema_version=SCHEMA_VERSION,
        deletion_pos_1=k,
        wt_length=wt_length,
        mutant_length=mutant_length,
        total_internal_nodes=len(records),
        valid_node_count=len(records) - len(invalid),
        invalid_node_count=len(invalid),
        invalid_without_listed_kind_count=invalid_unlabeled,
        error_kind_counts=kind_counts,
        invalid_nodes=tuple(invalid),
        first_invalid_span=first_invalid,
        narrowest_invalid_span=_pick_span(invalid, widest=False),
        widest_invalid_span=_pick_span(invalid, widest=True),
        invalid_contains_deletion_count=contains_ct,
        invalid_left_of_deletion_count=left_ct,
        invalid_right_of_deletion_count=right_ct,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _reconstruct_postorder(
    n: int, mutant_length: int, k: int
) -> list[tuple[int, int, int]]:
    """Post-order (lo, hi, survivor_leaf_count) over the mutant internal nodes.

    Rebuilds the exact topology :func:`check_deletion` evaluates using placeholder
    weights (spans/topology are weight-independent), including the singleton wrap
    for ``mutant_length == 1``. The walk order matches
    ``check_tree._collect_node_results_postorder`` (children before parent,
    left-to-right).
    """
    root = build_frozen_after_deletion_trits([0] * n, [0] * mutant_length, k)
    from mcore_py.model import Constituent  # local import: avoid hard import cycle

    out: list[tuple[int, int, int]] = []

    def walk(c: Any) -> None:
        for ch in c.children:
            if isinstance(ch, Constituent):
                walk(ch)
        idxs = descendant_orig_indices(c)
        out.append((idxs[0], idxs[-1], len(idxs)))

    walk(root)
    return out


def _classify_site(lo: int, hi: int, k: int) -> str:
    if hi < k:
        return "left"
    if lo > k:
        return "right"
    return "contains"  # lo <= k <= hi


def _pick_span(nodes: list[NodeRecord], *, widest: bool) -> Span | None:
    """Narrowest/widest invalid span.

    Deterministic tie-break rule (documented): among nodes of equal
    ``coordinate_width``, the smallest ``(leaf_lo, leaf_hi)`` wins — for both the
    narrowest and the widest selection.
    """
    if not nodes:
        return None
    if widest:
        best = min(nodes, key=lambda n: (-n.coordinate_width, n.leaf_lo, n.leaf_hi))
    else:
        best = min(nodes, key=lambda n: (n.coordinate_width, n.leaf_lo, n.leaf_hi))
    return (best.leaf_lo, best.leaf_hi)


def _span_to_list(span: Span | None) -> list[int] | None:
    return None if span is None else [span[0], span[1]]


def _rel_span(span: Span | None, k: int) -> list[int] | None:
    return None if span is None else [span[0] - k, span[1] - k]


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


__all__ = [
    "SCHEMA_VERSION",
    "NodeRecord",
    "DeletionShape",
    "node_records",
    "summarize_deletion_shape",
]
