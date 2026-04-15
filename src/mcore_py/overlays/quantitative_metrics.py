"""
QuantitativeMetrics Overlay — Indo-European (Spec Section 4)
==============================================================

Extends MCORE-1 for Indo-European quantitative meters. Defines:
  - Mora weight mapping (syllable type -> Trit)
  - Syncopation types (Kiparsky 2018)
  - Resolution rules
  - S3 emergence conditions
  - Cross-caesura constraint
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from mcore_py.model import Budget, Level, ProsodicUnit, Tension, Trit


# ---------------------------------------------------------------------------
# 4.1  Mora Weight Mapping
# ---------------------------------------------------------------------------

class SyllableType(Enum):
    """Syllable types in IE quantitative metrics."""
    OPEN_SHORT = auto()    # V         -> S1 (1 mora)
    CLOSED_OR_LONG = auto()  # VC or V̄   -> S2 (2 morae)
    SUPERHEAVY = auto()    # V̄C or CC  -> S3 (3 morae, tradition-dependent)


# Mapping: syllable type -> (Trit, mora_count)
WEIGHT_MAP: dict[SyllableType, tuple[Trit, int]] = {
    SyllableType.OPEN_SHORT:     (Trit.S1, 1),
    SyllableType.CLOSED_OR_LONG: (Trit.S2, 2),
    SyllableType.SUPERHEAVY:     (Trit.S3, 3),
}


def classify_syllable(
    vowel_long: bool,
    coda_present: bool,
    coda_cluster: bool = False,
) -> SyllableType:
    """Classify a syllable by its weight category.

    Parameters
    ----------
    vowel_long : bool
        Whether the vowel is long.
    coda_present : bool
        Whether the syllable has a coda consonant.
    coda_cluster : bool
        Whether the coda is a consonant cluster.

    Returns
    -------
    SyllableType
        The weight classification.

    Examples
    --------
    >>> classify_syllable(vowel_long=False, coda_present=False)
    <SyllableType.OPEN_SHORT: 1>
    >>> classify_syllable(vowel_long=True, coda_present=True)
    <SyllableType.SUPERHEAVY: 3>
    """
    if vowel_long and (coda_present or coda_cluster):
        return SyllableType.SUPERHEAVY
    elif vowel_long or coda_present:
        return SyllableType.CLOSED_OR_LONG
    else:
        return SyllableType.OPEN_SHORT


def syllable_weight(stype: SyllableType) -> Trit:
    """Get the Trit weight for a syllable type."""
    return WEIGHT_MAP[stype][0]


def syllable_morae(stype: SyllableType) -> int:
    """Get the mora count for a syllable type."""
    return WEIGHT_MAP[stype][1]


# ---------------------------------------------------------------------------
# 4.2  Syncopation Types (Kiparsky 2018)
# ---------------------------------------------------------------------------

class SyncopationType(Enum):
    """Canonical syncopation types in the IE iambic template.

    Syncopation is weight displacement between adjacent metrical positions.
    """
    CHORIAMBIC = auto()  # Positions 1-2: - u -> u -
    IONIC = auto()       # Positions 2-3: u - -> - u
    GLYCONIC = auto()    # Positions 3-4: - u -> u -
    NULL = auto()        # No syncopation


@dataclass(frozen=True)
class SyncopationPattern:
    """A syncopation between two adjacent positions.

    Attributes
    ----------
    stype : SyncopationType
        The canonical type.
    pos_a : int
        First position (0-indexed within the metron).
    pos_b : int
        Second position.
    tension_a : Tension
        Tension at position A (surplus if weight shifts away).
    tension_b : Tension
        Tension at position B (debt if weight shifts toward).
    """
    stype: SyncopationType
    pos_a: int
    pos_b: int
    tension_a: Tension
    tension_b: Tension


# Pre-built canonical patterns
SYNCOPATION_PATTERNS: dict[SyncopationType, SyncopationPattern] = {
    SyncopationType.CHORIAMBIC: SyncopationPattern(
        stype=SyncopationType.CHORIAMBIC,
        pos_a=0, pos_b=1,
        tension_a=Tension.SURPLUS, tension_b=Tension.DEBT,
    ),
    SyncopationType.IONIC: SyncopationPattern(
        stype=SyncopationType.IONIC,
        pos_a=1, pos_b=2,
        tension_a=Tension.SURPLUS, tension_b=Tension.DEBT,
    ),
    SyncopationType.GLYCONIC: SyncopationPattern(
        stype=SyncopationType.GLYCONIC,
        pos_a=2, pos_b=3,
        tension_a=Tension.SURPLUS, tension_b=Tension.DEBT,
    ),
}


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------

def resolve_heavy(unit: ProsodicUnit) -> tuple[ProsodicUnit, ProsodicUnit]:
    """Replace one heavy (S2) syllable with two light (S1) syllables.

    Resolution preserves total mora weight. The first light receives
    the original tension; the second is neutral.

    Parameters
    ----------
    unit : ProsodicUnit
        Must have weight S2.

    Returns
    -------
    tuple[ProsodicUnit, ProsodicUnit]
        Two S1 units replacing the original S2.

    Raises
    ------
    ValueError
        If unit weight is not S2.
    """
    if unit.weight != Trit.S2:
        raise ValueError(f"Resolution requires S2, got {unit.weight.name}")

    return (
        ProsodicUnit(
            weight=Trit.S1,
            tension=unit.tension,
            level=unit.level,
            label=f"{unit.label or ''}:res1" if unit.label else "res1",
        ),
        ProsodicUnit(
            weight=Trit.S1,
            tension=Tension.NEUTRAL,
            level=unit.level,
            label=f"{unit.label or ''}:res2" if unit.label else "res2",
        ),
    )


# ---------------------------------------------------------------------------
# Cross-caesura constraint
# ---------------------------------------------------------------------------

def check_cross_caesura(
    units: list[ProsodicUnit],
    caesura_position: int,
) -> bool:
    """Verify that no syncopation crosses a caesura boundary.

    Syncopation is blocked across caesurae in all attested IE metrical
    traditions (Kiparsky 2018). Caesurae act as implicit POP_FRAME /
    PUSH_FRAME boundaries.

    Parameters
    ----------
    units : list[ProsodicUnit]
        The metrical positions in a line.
    caesura_position : int
        Index of the caesura (boundary falls after this position).

    Returns
    -------
    bool
        True if no syncopation crosses the caesura.
    """
    for i in range(len(units) - 1):
        # Check if a tension pair spans the caesura
        if i == caesura_position:
            left = units[i]
            right = units[i + 1]
            if left.tension != Tension.NEUTRAL or right.tension != Tension.NEUTRAL:
                return False
    return True


# ---------------------------------------------------------------------------
# High-level overlay interface
# ---------------------------------------------------------------------------

class QuantitativeMetrics:
    """Overlay for Indo-European quantitative meters.

    Provides convenience methods for creating metrically well-formed
    constituents using IE conventions.
    """

    @staticmethod
    def syllable(
        vowel_long: bool = False,
        coda: bool = False,
        cluster: bool = False,
        tension: Tension = Tension.NEUTRAL,
    ) -> ProsodicUnit:
        """Create a prosodic unit from syllable properties."""
        stype = classify_syllable(vowel_long, coda, cluster)
        return ProsodicUnit(
            weight=syllable_weight(stype),
            tension=tension,
            level=Level.L1_AKSARA,
            features={"syllable_type": stype.name},
        )

    @staticmethod
    def foot(*syllables: ProsodicUnit, label: str | None = None) -> tuple[ProsodicUnit, list[ProsodicUnit]]:
        """Create a foot (L2) from syllables.

        Returns the parent unit and child list (for building a Constituent).
        """
        from mcore_py.algebra import trit_add_seq, OVERFLOW

        weights = [s.weight for s in syllables]
        pooled = trit_add_seq(list(weights))

        if pooled is OVERFLOW:
            raise ValueError(f"Foot overflow: syllable weights {[w.name for w in weights]}")

        parent = ProsodicUnit(
            weight=pooled,
            level=Level.L2_GANA,
            label=label,
        )
        return parent, list(syllables)

    @staticmethod
    def iambic_metron(
        syncopation: SyncopationType = SyncopationType.NULL,
    ) -> list[ProsodicUnit]:
        """Generate a 4-position iambic metron with optional syncopation.

        Default pattern: u - u - (S1 S2 S1 S2)
        """
        base = [
            ProsodicUnit(weight=Trit.S1, level=Level.L1_AKSARA),
            ProsodicUnit(weight=Trit.S2, level=Level.L1_AKSARA),
            ProsodicUnit(weight=Trit.S1, level=Level.L1_AKSARA),
            ProsodicUnit(weight=Trit.S2, level=Level.L1_AKSARA),
        ]

        if syncopation == SyncopationType.NULL:
            return base

        pattern = SYNCOPATION_PATTERNS.get(syncopation)
        if pattern is None:
            return base

        # Apply tension displacement
        base[pattern.pos_a].tension = pattern.tension_a
        base[pattern.pos_b].tension = pattern.tension_b

        return base
