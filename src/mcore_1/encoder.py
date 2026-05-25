"""
DNA → trit encoder with carry (MCORE-1 / GJB2 paper semantics).

Bases (value map): A=0, C=1, G=2, T=0 with **T-bias**
``ε_T(b) = 1`` if ``b`` is ``T`` or ``t``, else ``0``.

Per position (left-to-right scan)::

    u = v(b) + carry + ε_T(b)
    t = u mod 3
    carry = floor(u / 3)

The scan is an **associative semigroup action** on a finite carry state:
each step applies an element of a transformation semigroup
``(carry, trit) ↦ (carry', trit')`` determined by the current base.
Concatenating DNA symbols composes these steps in order.

This is **not** a monoid homomorphism from free-monoid concatenation of DNA
to trit strings: the visible output is a trit *and* a hidden carry, and
deletions / suffix edits generally invalidate naive substring closure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

_BASE_VALUE: dict[str, int] = {
    "A": 0,
    "C": 1,
    "G": 2,
    "T": 0,
    "a": 0,
    "c": 1,
    "g": 2,
    "t": 0,
}


def _eps_T(base: str) -> int:
    return 1 if base.upper() == "T" else 0


def base_value(base: str) -> int:
    """Ternary digit contribution ``v(b)`` before carry and T-bias."""
    if base not in _BASE_VALUE:
        raise ValueError(f"Invalid DNA base: {base!r}")
    return _BASE_VALUE[base]


@dataclass(frozen=True)
class EncodeStep:
    """One step of the carry scan."""

    index: int  # 0-based position in input
    base: str
    carry_in: int
    u: int
    trit: int  # 0, 1, or 2
    carry_out: int


def dna_to_trits(dna: str) -> tuple[list[int], list[EncodeStep]]:
    """Encode *dna* to trits with carry log.

    Returns
    -------
    trits : list[int]
        Length ``len(dna)``, values in ``{0, 1, 2}`` (S1/S2/S3 ordinals).
    log : list[EncodeStep]
        Per-position scan trace (``carry_in`` / ``carry_out`` are integers ≥ 0).
    """
    trits: list[int] = []
    log: list[EncodeStep] = []
    carry = 0
    for i, ch in enumerate(dna):
        v = base_value(ch)
        eps = _eps_T(ch)
        u = v + carry + eps
        t = u % 3
        carry_out = u // 3
        log.append(
            EncodeStep(
                index=i,
                base=ch,
                carry_in=carry,
                u=u,
                trit=t,
                carry_out=carry_out,
            )
        )
        trits.append(t)
        carry = carry_out
    return trits, log


def iter_encode_steps(dna: str) -> Iterator[EncodeStep]:
    """Yield :class:`EncodeStep` records (same semantics as :func:`dna_to_trits`)."""
    _, log = dna_to_trits(dna)
    yield from log
