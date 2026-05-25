"""Prefix / state composition checks (mirrors gjb2 ``checker.py`` spirit, not a duplicate)."""

from __future__ import annotations

import pytest

from mcore_1.encoder import dna_to_trits, iter_encode_steps


def _scan_with_initial_carry(dna: str, carry0: int) -> tuple[list[int], int]:
    trits: list[int] = []
    carry = carry0
    for ch in dna:
        from mcore_1.encoder import base_value

        eps = 1 if ch.upper() == "T" else 0
        v = base_value(ch)
        u = v + carry + eps
        trits.append(u % 3)
        carry = u // 3
    return trits, carry


def test_split_scan_matches_full_scan() -> None:
    """Encoding ``prefix+suffix`` equals scanning suffix with carry carried out from prefix."""
    dna = "ACGTACGTACGTACGTACGTACGTACGTACGT"
    mid = 10
    prefix, suffix = dna[:mid], dna[mid:]
    full_trits, _ = dna_to_trits(dna)
    pre_trits, pre_log = dna_to_trits(prefix)
    carry_after_prefix = pre_log[-1].carry_out if pre_log else 0
    suffix_trits, _ = _scan_with_initial_carry(suffix, carry_after_prefix)
    assert full_trits == pre_trits + suffix_trits


def test_step_iterator_matches_trits() -> None:
    dna = "TGCA"
    trits, log = dna_to_trits(dna)
    assert [s.trit for s in log] == trits
    assert list(iter_encode_steps(dna)) == log


@pytest.mark.parametrize("dna", ["A", "TTTT", "GATTACA"])
def test_valid_bases_encode(dna: str) -> None:
    dna_to_trits(dna)


def test_invalid_base_raises() -> None:
    with pytest.raises(ValueError):
        dna_to_trits("NN")
