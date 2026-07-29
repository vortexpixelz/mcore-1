"""PSA-001A exhaustive shard-invariance test for the current DNA encoder.

The result is intentionally a bounded null: the only reachable carry state is
zero, so explicit state handoff and naive chunking are equivalent for this
transform.  This test must not be cited as evidence for nontrivial carry
propagation or generalized distributed-system resilience.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from mcore_1.psa001_sharding import (
    BoundaryState,
    run_dna_monolithic,
    run_dna_shard,
    run_dna_two_shards,
)

FIXTURE_PATH = Path(__file__).parents[1] / "experiments/PSA-001/fixtures/dna_128.txt"
FIXTURE_SHA256 = "ec4fec99482dc489f8006c8c2544bc5b25ee610aaa930a862b2f8ae59566e4a5"
SUBSTITUTION = {"A": "C", "C": "G", "G": "T", "T": "A"}


def _fixture() -> str:
    dna = FIXTURE_PATH.read_text(encoding="utf-8").strip()
    assert len(dna) == 128
    assert set(dna) <= set(SUBSTITUTION)
    return dna


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _substitute(dna: str, position: int) -> str:
    return dna[:position] + SUBSTITUTION[dna[position]] + dna[position + 1 :]


def _assert_equivalent(dna: str, boundary: int) -> None:
    monolithic_output, monolithic_state, _ = run_dna_monolithic(dna)
    recomposed_output, recomposed_state, _ = run_dna_two_shards(dna, boundary)

    assert recomposed_output == monolithic_output
    assert recomposed_state == monolithic_state == BoundaryState()
    assert recomposed_state.sha256() == monolithic_state.sha256()

    # Conventional naive chunking baseline.  It matches only because carry=0
    # is the sole reachable state for this particular transform/input domain.
    left_output, _, _ = run_dna_shard(dna[:boundary], BoundaryState())
    right_output, _, _ = run_dna_shard(dna[boundary:], BoundaryState())
    assert left_output + right_output == monolithic_output


def test_psa001_fixture_is_pinned() -> None:
    dna = _fixture()
    assert _sha256_text(dna) == FIXTURE_SHA256


def test_psa001_boundary_contract_fails_closed() -> None:
    state = BoundaryState()
    assert state.carry == 0
    assert state.sha256() == BoundaryState().sha256()

    with pytest.raises(ValueError, match="Nonzero carry is unreachable"):
        run_dna_shard("ACGT", BoundaryState(carry=1))

    with pytest.raises(ValueError, match="Unsupported boundary schema"):
        run_dna_shard("ACGT", BoundaryState(schema_version="unknown"))


def test_psa001_complete_matrix_is_bounded_null() -> None:
    dna = _fixture()
    comparisons = 0

    # 127 unperturbed split comparisons.
    for boundary in range(1, len(dna)):
        _assert_equivalent(dna, boundary)
        comparisons += 1

    # 128 deterministic substitutions x 127 split boundaries = 16,256.
    for position in range(len(dna)):
        perturbed = _substitute(dna, position)
        for boundary in range(1, len(perturbed)):
            _assert_equivalent(perturbed, boundary)
            comparisons += 1

    assert comparisons == 127 + (128 * 127) == 16_383
