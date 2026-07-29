"""PSA-001 adapter for testing shard invariance of the current DNA encoder.

This module deliberately preserves the semantics of :func:`dna_to_trits`.
The current DNA mapping has one reachable boundary state, carry=0.  The
adapter makes that degenerate state explicit so the exhaustive assay can be
run without manufacturing a carry effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

from mcore_1.encoder import EncodeStep, dna_to_trits

SCHEMA_VERSION = "psa001-boundary-v1"
TRANSFORM_ID = "mcore_1.encoder.dna_to_trits"


@dataclass(frozen=True)
class BoundaryState:
    """Serializable boundary state for the current carry-inert DNA encoder."""

    schema_version: str = SCHEMA_VERSION
    transform_id: str = TRANSFORM_ID
    carry: int = 0

    def canonical_json(self) -> str:
        """Return deterministic JSON suitable for hashing and receipts."""
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))

    def sha256(self) -> str:
        """Return the SHA-256 of the canonical boundary representation."""
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def run_dna_shard(
    dna: str,
    start_state: BoundaryState,
) -> tuple[list[int], BoundaryState, tuple[EncodeStep, ...]]:
    """Encode one DNA shard under an explicit, fail-closed boundary contract.

    Nonzero carry is rejected because it is not reachable through the public
    DNA encoder and the public encoder exposes no start-state parameter.
    """
    if start_state.schema_version != SCHEMA_VERSION:
        raise ValueError(f"Unsupported boundary schema: {start_state.schema_version!r}")
    if start_state.transform_id != TRANSFORM_ID:
        raise ValueError(f"Unsupported transform: {start_state.transform_id!r}")
    if start_state.carry != 0:
        raise ValueError("Nonzero carry is unreachable for the current DNA encoder")

    output, log = dna_to_trits(dna)
    end_carry = log[-1].carry_out if log else start_state.carry
    if any(step.carry_in != 0 or step.carry_out != 0 for step in log):
        raise AssertionError("Current carry-inert invariant was violated")

    return output, BoundaryState(carry=end_carry), tuple(log)


def run_dna_monolithic(
    dna: str,
) -> tuple[list[int], BoundaryState, tuple[EncodeStep, ...]]:
    """Run the fixed transform over the whole input."""
    return run_dna_shard(dna, BoundaryState())


def run_dna_two_shards(
    dna: str,
    boundary: int,
) -> tuple[list[int], BoundaryState, tuple[EncodeStep, ...]]:
    """Run two shards with an explicit boundary-state handoff and recompose."""
    if not 1 <= boundary < len(dna):
        raise ValueError("boundary must be inside the DNA fixture")

    left_output, boundary_state, left_log = run_dna_shard(dna[:boundary], BoundaryState())
    right_output, end_state, right_log = run_dna_shard(dna[boundary:], boundary_state)
    return left_output + right_output, end_state, left_log + right_log
