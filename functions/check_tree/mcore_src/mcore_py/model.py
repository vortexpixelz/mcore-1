"""
MCORE-1 Data Model (Spec Section 2)
====================================

Defines the fundamental types: Trit, Tension, Level, ProsodicUnit,
Constituent, Budget, EdgeLicense, and HierarchyMap.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any


# ---------------------------------------------------------------------------
# 3.1  The Trit Set  T = {0, 1, 2}
# ---------------------------------------------------------------------------

class Trit(IntEnum):
    """Ternary weight state (Spec §3.1).

    Values are ordinal weight classes, not mora counts.
    The mapping to mora counts is overlay-dependent.
    """
    S1 = 0  # light  — default: monomoraic
    S2 = 1  # heavy  — default: bimoraic
    S3 = 2  # superheavy — default: trimoraic


class Tension(IntEnum):
    """Tension state for debt/surplus resolution (Spec §3.2.2)."""
    DEBT = -1
    NEUTRAL = 0
    SURPLUS = 1


# ---------------------------------------------------------------------------
# 2.4  HierarchyMap — five canonical levels
# ---------------------------------------------------------------------------

class Level(IntEnum):
    """Hierarchy level (Spec §2.4).

    Sanskrit terms are canonical; overlays define tradition-specific aliases.
    """
    L0_MATRA = 0   # mora       — minimal weight-bearing unit
    L1_AKSARA = 1  # syllable   — grouping of morae
    L2_GANA = 2    # foot       — grouping of syllables
    L3_PADA = 3    # line       — grouping of feet
    L4_SLOKA = 4   # stanza     — grouping of lines


class HierarchyMap:
    """Maps between canonical Sanskrit names, English names, and levels."""

    _CANONICAL: dict[Level, tuple[str, str]] = {
        Level.L0_MATRA:  ("matra",  "mora"),
        Level.L1_AKSARA: ("aksara", "syllable"),
        Level.L2_GANA:   ("gana",   "foot"),
        Level.L3_PADA:   ("pada",   "line"),
        Level.L4_SLOKA:  ("sloka",  "stanza"),
    }

    def __init__(self, aliases: dict[Level, tuple[str, str]] | None = None) -> None:
        self._map = dict(self._CANONICAL)
        if aliases:
            self._map.update(aliases)

    def sanskrit(self, level: Level) -> str:
        return self._map[level][0]

    def english(self, level: Level) -> str:
        return self._map[level][1]

    def from_name(self, name: str) -> Level:
        """Look up a level by any registered name (case-insensitive)."""
        name_lower = name.lower()
        for lvl, (skt, eng) in self._map.items():
            if name_lower in (skt.lower(), eng.lower(), lvl.name.lower()):
                return lvl
        raise KeyError(f"Unknown level name: {name!r}")


# ---------------------------------------------------------------------------
# 2.3  Budget
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Budget:
    """Weight constraint on a Constituent's children (Spec §2.3).

    Parameters
    ----------
    min_weight : Trit
        Minimum total weight.
    max_weight : Trit | None
        Maximum total weight.  None = unbounded.
    unit : Level
        Hierarchy level for counting.
    exact : bool
        If True, total must equal max_weight exactly.
    """
    min_weight: Trit
    max_weight: Trit | None = None
    unit: Level = Level.L0_MATRA
    exact: bool = False

    def satisfied(self, total: int) -> bool:
        """Check whether *total* weight satisfies this budget."""
        if total < self.min_weight:
            return False
        if self.max_weight is not None and total > self.max_weight:
            return False
        if self.exact and self.max_weight is not None and total != self.max_weight:
            return False
        return True


# ---------------------------------------------------------------------------
# 2.2  EdgeLicense
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EdgeLicense:
    """Boundary behavior for a Constituent edge (Spec §2.2).

    Parameters
    ----------
    position : str
        "left" or "right"
    allows_anceps : bool
        Whether the edge position can be realized as either heavy or light.
    allows_catalexis : bool
        Whether the edge position can be empty.
    allows_brevis_in_longo : bool
        Whether a short syllable can occupy a long position at colon end.
    """
    position: str = "right"
    allows_anceps: bool = False
    allows_catalexis: bool = False
    allows_brevis_in_longo: bool = False


# ---------------------------------------------------------------------------
# 2.1  ProsodicUnit
# ---------------------------------------------------------------------------

@dataclass
class ProsodicUnit:
    """Fundamental unit of the data model (Spec §2.1).

    Every element in a metrical structure is a ProsodicUnit.

    Parameters
    ----------
    weight : Trit
        Ternary weight value.
    tension : Tension
        Debt/neutral/surplus state.
    level : Level
        Position in the hierarchy.
    label : str | None
        Optional human-readable label.
    features : dict[str, Any]
        Overlay-defined key-value features.
    id : str
        Unique identifier (auto-generated UUID).
    """
    weight: Trit = Trit.S1
    tension: Tension = Tension.NEUTRAL
    level: Level = Level.L0_MATRA
    label: str | None = None
    features: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __repr__(self) -> str:
        t_str = {Tension.DEBT: "-", Tension.NEUTRAL: "0", Tension.SURPLUS: "+"}[self.tension]
        return f"PU({self.weight.name}, t={t_str}, {self.level.name})"


# ---------------------------------------------------------------------------
# 2.2  Constituent
# ---------------------------------------------------------------------------

@dataclass
class Constituent:
    """An ordered sequence of ProsodicUnits forming a metrical group (Spec §2.2).

    Parameters
    ----------
    parent : ProsodicUnit
        The internal node representing this constituent.
    children : list[ProsodicUnit | Constituent]
        Ordered child elements (leaves or nested constituents).
    budget : Budget | None
        Weight constraint on children.
    edge : EdgeLicense | None
        Boundary behavior.
    defers : list[tuple[Tension, Level]]
        Unresolved tension defers (Spec §3.4, Option B).
    """
    parent: ProsodicUnit
    children: list[ProsodicUnit | Constituent] = field(default_factory=list)
    budget: Budget | None = None
    edge: EdgeLicense | None = None
    defers: list[tuple[Tension, Level]] = field(default_factory=list)

    def add_child(self, child: ProsodicUnit | Constituent) -> None:
        """Append a child to this constituent."""
        self.children.append(child)

    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0

    def child_weights(self) -> list[Trit]:
        """Extract the weight of each child."""
        weights: list[Trit] = []
        for c in self.children:
            if isinstance(c, Constituent):
                weights.append(c.parent.weight)
            else:
                weights.append(c.weight)
        return weights

    def __repr__(self) -> str:
        return (
            f"Constituent({self.parent.level.name}, "
            f"children={len(self.children)}, "
            f"w={self.parent.weight.name})"
        )
