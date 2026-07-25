"""DNA carry-inert invariant (executable, not prose).

Under the current DNA mapping (A=0, C=1, G=2, T=0 with T-bias +1), the encoder
is **state-compatible but carry-inert on valid DNA input**: starting from carry
0, every base leaves carry 0, so no string over ``{A, C, G, T}`` ever produces a
nonzero carry. Any deletion error geometry observed downstream therefore must
**not** be attributed to a DNA encoder carry effect.

The carry machinery itself is retained; these tests only make the present
invariant impossible to miss.
"""

from __future__ import annotations

import random

from mcore_1.encoder import dna_to_trits, iter_encode_steps

DNA = "ACGT"


def test_one_step_carry_closure_from_zero() -> None:
    """Transition closure: from ``carry_in == 0``, each base maps to ``carry_out == 0``."""
    for base in "ACGTacgt":
        (step,) = list(iter_encode_steps(base))
        assert step.carry_in == 0
        assert step.carry_out == 0, f"{base!r} produced nonzero carry {step.carry_out}"


def test_max_single_step_u_stays_sub_ternary() -> None:
    """Mechanism: from carry 0, the largest single-step ``u`` is 2 (G) or 1 (T)."""
    for base in DNA:
        (step,) = list(iter_encode_steps(base))
        assert step.u < 3
        assert step.carry_out == step.u // 3 == 0


def test_zero_is_the_only_reachable_carry_state() -> None:
    """0 is an absorbing fixed point, so every step of any DNA string stays at 0.

    Because ``0 -> 0`` for every base, no reachable carry other than 0 exists on
    valid DNA input. We verify ``carry_in == carry_out == 0`` at *every* step for
    representative and randomized strings.
    """
    samples = [
        "ATG" + "ACGT" * 20,
        "GGGGGGGGGGG",  # all G — the maximal single-base value (2)
        "TTTTTTTTTTT",  # all T — value 0 plus T-bias 1
        "ATGGATTGGGGCAAAGAGGCAGAGAAACACAAACGCAGACT",  # GJB2-style fragment
    ]
    rng = random.Random(1234)
    samples += [
        "".join(rng.choice(DNA) for _ in range(rng.randint(1, 300))) for _ in range(50)
    ]
    for seq in samples:
        _, log = dna_to_trits(seq)
        assert all(s.carry_in == 0 and s.carry_out == 0 for s in log), seq[:24]
