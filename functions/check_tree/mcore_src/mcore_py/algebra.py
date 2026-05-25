"""
Trit Algebra (Spec Section 3)
==============================

Defines the four operations on the trit set T = {0, 1, 2}:
  +     addition (mora pooling)
  x     tension pairing (debt/surplus resolution)
  pi_L  projection (weight at a hierarchy level)
  *     completion (generalized Pingala prastara)
"""

from __future__ import annotations

from typing import Sequence

from mcore_py.model import (
    Budget,
    Constituent,
    Level,
    ProsodicUnit,
    Tension,
    Trit,
)


# ---------------------------------------------------------------------------
# Sentinel for overflow
# ---------------------------------------------------------------------------

class _Overflow:
    """Sentinel representing budget overflow (Spec §3.2.1).

    The addition table produces overflow when the sum exceeds S3.
    Overflow is an error state, not a valid Trit.
    """

    _instance: _Overflow | None = None

    def __new__(cls) -> _Overflow:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "OVERFLOW"

    def __bool__(self) -> bool:
        return False  # falsy — convenient for error checks


OVERFLOW = _Overflow()


# ---------------------------------------------------------------------------
# 3.2.1  Addition (mora pooling)
# ---------------------------------------------------------------------------

# Pre-computed addition table  (Spec §3.2.1)
# Row = left operand, Col = right operand
# None entries = overflow
_ADD_TABLE: list[list[Trit | None]] = [
    #       S1      S2      S3
    [Trit.S2, Trit.S3, None],       # S1 + ...
    [Trit.S3, None,    None],       # S2 + ...
    [None,    None,    None],       # S3 + ...
]


def trit_add(a: Trit, b: Trit) -> Trit | _Overflow:
    """Add two trits (mora pooling).

    Returns OVERFLOW if the sum exceeds S3.

    The algebraic structure (T, +) is a partial commutative semigroup:
    commutative, associative (where defined), no identity, no zero.

    Examples
    --------
    >>> trit_add(Trit.S1, Trit.S1)
    <Trit.S2: 1>
    >>> trit_add(Trit.S2, Trit.S2)
    OVERFLOW
    """
    result = _ADD_TABLE[a.value][b.value]
    if result is None:
        return OVERFLOW
    return result


def trit_add_seq(trits: Sequence[Trit]) -> Trit | _Overflow:
    """Left-fold addition over a sequence of trits.

    Returns OVERFLOW on first overflow encountered.

    Examples
    --------
    >>> trit_add_seq([Trit.S1, Trit.S1, Trit.S1])
    OVERFLOW
    >>> trit_add_seq([Trit.S1, Trit.S2])
    <Trit.S3: 2>
    """
    if len(trits) == 0:
        raise ValueError("Cannot add an empty sequence of trits")
    if len(trits) == 1:
        return trits[0]

    acc: Trit | _Overflow = trits[0]
    for t in trits[1:]:
        if isinstance(acc, _Overflow):
            return OVERFLOW
        acc = trit_add(acc, t)
    return acc


# ---------------------------------------------------------------------------
# 3.2.2  Tension pairing
# ---------------------------------------------------------------------------

def tension_pair(
    w1: Trit,
    t1: Tension,
    w2: Trit,
    t2: Tension,
    parent_budget: Budget | None = None,
) -> bool:
    """Validate debt/surplus resolution between adjacent prosodic units.

    Returns True iff:
      - t1 + t2 == 0  (tension cancels)
      - w1 + w2 does not overflow (and satisfies parent budget, if given)

    Parameters
    ----------
    w1, t1 : weight and tension of the first unit
    w2, t2 : weight and tension of the second unit
    parent_budget : optional Budget to check against
    """
    if t1.value + t2.value != 0:
        return False

    combined = trit_add(w1, w2)
    if isinstance(combined, _Overflow):
        return False

    if parent_budget is not None:
        return parent_budget.satisfied(combined.value)

    return True


# ---------------------------------------------------------------------------
# 3.2.3  Projection  pi_L
# ---------------------------------------------------------------------------

def project(node: Constituent | ProsodicUnit, target_level: Level) -> int:
    """Extract the total weight contribution at a specific hierarchy level.

    Recursively sums child weights at or below the target level.

    Parameters
    ----------
    node : Constituent or ProsodicUnit
        The root of the subtree to project.
    target_level : Level
        The hierarchy level to project onto.

    Returns
    -------
    int
        Total mora-equivalent weight at the target level.
    """
    if isinstance(node, ProsodicUnit):
        if node.level <= target_level:
            return node.weight.value
        return 0

    # Constituent
    if node.parent.level < target_level:
        return 0

    total = 0
    for child in node.children:
        total += project(child, target_level)
    return total


# ---------------------------------------------------------------------------
# 3.2.4  Completion  *  (Generalized Prastara)
# ---------------------------------------------------------------------------

def complete(
    partial: list[Trit | None],
    budget: Budget,
    constraints: list | None = None,
) -> list[list[Trit]]:
    """Generate all valid completions of a partial metrical pattern.

    Generalizes Pingala's prastara (enumeration) algorithm to ternary states.
    Complexity: worst case 3^n; with budget pruning, bounded by O(n^k)
    for fixed budget k (Spec §10.2).

    Parameters
    ----------
    partial : list of Trit | None
        Partially filled pattern. None = unfilled position.
    budget : Budget
        Weight constraint to satisfy.
    constraints : list, optional
        Additional constraint functions (reserved for overlays).

    Returns
    -------
    list[list[Trit]]
        All valid completed patterns.

    Examples
    --------
    >>> from mcore_py.model import Budget, Trit, Level
    >>> b = Budget(min_weight=Trit.S2, max_weight=Trit.S2, unit=Level.L0_MATRA, exact=True)
    >>> results = complete([None, None], b)
    >>> [Trit.S1, Trit.S1] in results
    True
    """
    return _complete_recurse(partial, budget, constraints or [])


def _complete_recurse(
    partial: list[Trit | None],
    budget: Budget,
    constraints: list,
) -> list[list[Trit]]:
    """Recursive backtracking completion with pruning."""
    # Find first unfilled position
    idx: int | None = None
    for i, v in enumerate(partial):
        if v is None:
            idx = i
            break

    if idx is None:
        # All positions filled — validate
        filled = [t for t in partial if t is not None]
        total = sum(t.value for t in filled)
        if budget.satisfied(total):
            if all(c(filled) for c in constraints):
                return [list(filled)]  # type: ignore[arg-type]
        return []

    # Count filled weight and remaining positions
    filled_weight = sum(t.value for t in partial if t is not None)
    remaining = sum(1 for t in partial if t is None)

    results: list[list[Trit]] = []
    for w in (Trit.S1, Trit.S2, Trit.S3):
        # Pruning: lower bound check
        # Minimum possible total = filled + w + S1 * (remaining - 1)
        min_possible = filled_weight + w.value + Trit.S1.value * (remaining - 1)
        if budget.max_weight is not None and min_possible > budget.max_weight.value:
            continue

        # Pruning: upper bound check
        # Maximum possible total = filled + w + S3 * (remaining - 1)
        max_possible = filled_weight + w.value + Trit.S3.value * (remaining - 1)
        if max_possible < budget.min_weight.value:
            continue

        candidate = list(partial)
        candidate[idx] = w
        results.extend(_complete_recurse(candidate, budget, constraints))

    return results


# ---------------------------------------------------------------------------
# Convenience: enumerate all patterns of length n for a given budget
# ---------------------------------------------------------------------------

def enumerate_patterns(n: int, budget: Budget) -> list[list[Trit]]:
    """Enumerate all valid metrical patterns of length *n* for *budget*.

    This is the full prastara — Pingala's algorithm generalized to ternary.

    Parameters
    ----------
    n : int
        Number of positions.
    budget : Budget
        Weight constraint.

    Returns
    -------
    list[list[Trit]]
        All valid patterns.
    """
    partial: list[Trit | None] = [None] * n
    return complete(partial, budget)
