"""
QuantumResourceMetrics Overlay — MCORE-Q (Spec Extension)
==========================================================

Extends MCORE-1 for quantum OS resource scheduling. Defines:
  - Qubit state weight mapping  (fidelity -> Trit)
  - Scheduling frame construction (task slots, circuit layers)
  - Budget constraints for qubit allocation
  - Hierarchy aliases: mora->qubit_slot, foot->scheduling_frame, stanza->circuit

The fundamental isomorphism (MCORE-Q §2):
  Trit S1 (light)       =  IDLE qubit         (fidelity < 0.70)
  Trit S2 (heavy)       =  OPERATIONAL qubit  (0.70 <= fidelity < 0.90)
  Trit S3 (superheavy)  =  ENTANGLED qubit    (fidelity >= 0.90)

A scheduling frame is well-formed iff check_tree() returns valid —
the same conservation law that validates a Sanskrit metrical foot.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Sequence

from mcore_py.model import (
    Budget,
    Constituent,
    HierarchyMap,
    Level,
    ProsodicUnit,
    Tension,
    Trit,
)


# ---------------------------------------------------------------------------
# Fidelity thresholds
# ---------------------------------------------------------------------------

FIDELITY_IDLE_MAX: float = 0.70        # below this -> IDLE (S1)
FIDELITY_OPERATIONAL_MAX: float = 0.90  # below this -> OPERATIONAL (S2)
                                         # at or above -> ENTANGLED (S3)


# ---------------------------------------------------------------------------
# Qubit state enum
# ---------------------------------------------------------------------------

class QubitState(Enum):
    """Ternary qubit resource state.

    Maps directly onto MCORE-1 trit values:
      IDLE         ->  Trit.S1  (light)       fidelity < 0.70
      OPERATIONAL  ->  Trit.S2  (heavy)       0.70 <= fidelity < 0.90
      ENTANGLED    ->  Trit.S3  (superheavy)  fidelity >= 0.90
    """
    IDLE = auto()         # Below threshold — not assigned to active tasks
    OPERATIONAL = auto()  # Standard compute — single-qubit gates
    ENTANGLED = auto()    # High-fidelity — multi-qubit / entangling gates


# Canonical weight map: QubitState -> Trit
QUBIT_WEIGHT_MAP: dict[QubitState, Trit] = {
    QubitState.IDLE:        Trit.S1,
    QubitState.OPERATIONAL: Trit.S2,
    QubitState.ENTANGLED:   Trit.S3,
}


def classify_qubit(fidelity: float) -> QubitState:
    """Classify a qubit's resource state from its fidelity score.

    Parameters
    ----------
    fidelity : float
        Qubit fidelity in [0.0, 1.0]. Typically reported by hardware
        calibration or a quantum OS scheduler (e.g. Origin Pilot).

    Returns
    -------
    QubitState
        The ternary resource state.

    Raises
    ------
    ValueError
        If fidelity is outside [0.0, 1.0].

    Examples
    --------
    >>> classify_qubit(0.50)
    <QubitState.IDLE: 1>
    >>> classify_qubit(0.80)
    <QubitState.OPERATIONAL: 2>
    >>> classify_qubit(0.95)
    <QubitState.ENTANGLED: 3>
    """
    if not 0.0 <= fidelity <= 1.0:
        raise ValueError(f"fidelity must be in [0.0, 1.0], got {fidelity}")
    if fidelity < FIDELITY_IDLE_MAX:
        return QubitState.IDLE
    if fidelity < FIDELITY_OPERATIONAL_MAX:
        return QubitState.OPERATIONAL
    return QubitState.ENTANGLED


def qubit_weight(state: QubitState) -> Trit:
    """Return the Trit weight for a qubit state."""
    return QUBIT_WEIGHT_MAP[state]


# ---------------------------------------------------------------------------
# Hierarchy map — quantum terminology aliases
# ---------------------------------------------------------------------------

QUANTUM_HIERARCHY: HierarchyMap = HierarchyMap(
    aliases={
        Level.L0_MATRA:  ("qubit_slot",       "qubit slot"),
        Level.L1_AKSARA: ("task_slot",         "task slot"),
        Level.L2_GANA:   ("scheduling_frame",  "scheduling frame"),
        Level.L3_PADA:   ("circuit_layer",     "circuit layer"),
        Level.L4_SLOKA:  ("circuit",           "circuit"),
    }
)


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------

def qubit_slot(
    fidelity: float,
    label: str | None = None,
    tension: Tension = Tension.NEUTRAL,
) -> ProsodicUnit:
    """Create a ProsodicUnit representing one qubit assignment (L0: qubit slot).

    Parameters
    ----------
    fidelity : float
        Raw fidelity in [0.0, 1.0] from hardware or scheduler.
    label : str | None
        Optional qubit identifier (e.g. "q0", "q3").
    tension : Tension
        Tension state for decoherence displacement tracking.

    Returns
    -------
    ProsodicUnit
        At Level.L0_MATRA (qubit slot), weight derived from fidelity.
    """
    state = classify_qubit(fidelity)
    return ProsodicUnit(
        weight=qubit_weight(state),
        tension=tension,
        level=Level.L0_MATRA,
        label=label,
        features={"fidelity": fidelity, "qubit_state": state.name},
    )


def task_slot(
    *qubits: ProsodicUnit,
    label: str | None = None,
) -> tuple[ProsodicUnit, list[ProsodicUnit]]:
    """Create a task slot (L1) from one or more qubit slots.

    A task slot represents the qubit resources consumed by a single
    quantum task (gate application or measurement) within a scheduling
    frame. Mirrors QuantitativeMetrics.foot(): returns (parent, children)
    for Constituent construction.

    Parameters
    ----------
    *qubits : ProsodicUnit
        One or more qubit-slot ProsodicUnits (L0_MATRA).
    label : str | None
        Optional task label (e.g. "CNOT_q0q1").

    Returns
    -------
    tuple[ProsodicUnit, list[ProsodicUnit]]
        Parent unit at L1_AKSARA and ordered child list.

    Raises
    ------
    ValueError
        If combined qubit weights overflow S3 — split into multiple slots.
    """
    from mcore_py.algebra import OVERFLOW, trit_add_seq

    weights = [q.weight for q in qubits]
    pooled = trit_add_seq(list(weights))

    if pooled is OVERFLOW:
        raise ValueError(
            f"Task slot overflow: qubit weights {[w.name for w in weights]} "
            f"exceed S3 budget. Split into multiple task slots."
        )

    parent = ProsodicUnit(
        weight=pooled,
        level=Level.L1_AKSARA,
        label=label,
        features={"task_qubit_count": len(qubits)},
    )
    return parent, list(qubits)


def scheduling_frame(
    *tasks: tuple[ProsodicUnit, list[ProsodicUnit]],
    budget: Budget | None = None,
    label: str | None = None,
) -> Constituent:
    """Build a scheduling frame (L2) from task slots.

    A scheduling frame is one time slice of the quantum scheduler —
    analogous to a metrical foot. It is well-formed iff check_tree()
    returns valid, enforcing the same mora conservation law that
    validates Vedic meters.

    Parameters
    ----------
    *tasks : tuple[ProsodicUnit, list[ProsodicUnit]]
        Task slots as returned by task_slot().
    budget : Budget | None
        Optional resource budget. If None, only mora conservation
        is enforced.
    label : str | None
        Optional frame label.

    Returns
    -------
    Constituent
        A complete L2 Constituent ready for check_tree() validation.

    Raises
    ------
    ValueError
        If no tasks are provided, or if combined task weights exceed S3.
    """
    from mcore_py.algebra import OVERFLOW, trit_add_seq

    if not tasks:
        raise ValueError("scheduling_frame requires at least one task slot.")

    task_parents = [t[0] for t in tasks]
    task_weights = [p.weight for p in task_parents]
    pooled = trit_add_seq(task_weights)

    if pooled is OVERFLOW:
        raise ValueError(
            f"Scheduling frame overflow: task weights "
            f"{[w.name for w in task_weights]} exceed S3. "
            f"Distribute tasks across multiple frames."
        )

    frame_parent = ProsodicUnit(
        weight=pooled,
        level=Level.L2_GANA,
        label=label,
        features={"task_count": len(tasks)},
    )

    children: list[Constituent] = [
        Constituent(parent=task_parent, children=list(task_qubits))
        for task_parent, task_qubits in tasks
    ]

    return Constituent(
        parent=frame_parent,
        children=children,
        budget=budget,
    )


# ---------------------------------------------------------------------------
# High-level overlay class
# ---------------------------------------------------------------------------

class QuantumResourceMetrics:
    """Overlay for quantum OS resource scheduling.

    Translates quantum scheduler state into MCORE-1 structures for
    check_tree() validation. The same conservation law that determines
    whether a Sanskrit foot is metrically valid determines whether a
    quantum scheduling frame is resource-valid.

    Hierarchy:
      L0  qubit_slot       one qubit's fidelity state
      L1  task_slot        one task's qubit resource footprint
      L2  scheduling_frame one time slice (validated by check_tree)
      L3  circuit_layer    collection of frames at one circuit depth
      L4  circuit          full quantum circuit / job
    """

    HIERARCHY: HierarchyMap = QUANTUM_HIERARCHY

    @staticmethod
    def qubit(
        fidelity: float,
        label: str | None = None,
        tension: Tension = Tension.NEUTRAL,
    ) -> ProsodicUnit:
        """Create a qubit slot from a fidelity score."""
        return qubit_slot(fidelity, label=label, tension=tension)

    @staticmethod
    def task(
        *qubits: ProsodicUnit,
        label: str | None = None,
    ) -> tuple[ProsodicUnit, list[ProsodicUnit]]:
        """Create a task slot from qubit slots."""
        return task_slot(*qubits, label=label)

    @staticmethod
    def frame(
        *tasks: tuple[ProsodicUnit, list[ProsodicUnit]],
        budget: Budget | None = None,
        label: str | None = None,
    ) -> Constituent:
        """Build a scheduling frame from task slots."""
        return scheduling_frame(*tasks, budget=budget, label=label)

    @staticmethod
    def from_fidelity_list(
        fidelities: Sequence[float],
        labels: Sequence[str] | None = None,
        budget: Budget | None = None,
        frame_label: str | None = None,
    ) -> Constituent:
        """Build a scheduling frame directly from a list of fidelity values.

        Each fidelity becomes one qubit slot in its own task slot, all
        collected into a single scheduling frame. Convenient for feeding
        raw scheduler output directly into check_tree().

        Parameters
        ----------
        fidelities : Sequence[float]
            Per-qubit fidelity scores in [0.0, 1.0].
        labels : Sequence[str] | None
            Optional qubit labels. Must match len(fidelities) if provided.
        budget : Budget | None
            Optional resource budget for the frame.
        frame_label : str | None
            Optional label for the frame.

        Returns
        -------
        Constituent
            A scheduling frame ready for check_tree() validation.

        Examples
        --------
        >>> from mcore_py.checker import check_tree
        >>> frame = QuantumResourceMetrics.from_fidelity_list([0.50, 0.80])
        >>> check_tree(frame).valid
        True
        """
        if labels is not None and len(labels) != len(fidelities):
            raise ValueError(
                f"labels length {len(labels)} != fidelities length {len(fidelities)}"
            )

        tasks = []
        for i, f in enumerate(fidelities):
            lbl = labels[i] if labels is not None else f"q{i}"
            q = qubit_slot(f, label=lbl)
            tasks.append(task_slot(q, label=f"task_{lbl}"))

        return scheduling_frame(*tasks, budget=budget, label=frame_label)

    @staticmethod
    def decoherence_trajectory(
        initial_fidelities: Sequence[float],
        decay_rate: float = 0.05,
        steps: int = 5,
    ) -> list[list[QubitState]]:
        """Model qubit state degradation as a ternary trit trajectory.

        Applies linear fidelity decay at each step and classifies the
        resulting state. This is the quantum analogue of crystallization:
        a state space converging downward under noise, expressible in
        the same ternary algebra used for metrical pattern analysis.

        Parameters
        ----------
        initial_fidelities : Sequence[float]
            Starting fidelity for each qubit in [0.0, 1.0].
        decay_rate : float
            Fidelity reduction per step (default 0.05 = 5% per step).
        steps : int
            Number of time steps to simulate.

        Returns
        -------
        list[list[QubitState]]
            Outer list = time steps, inner list = per-qubit QubitState.
        """
        trajectory: list[list[QubitState]] = []
        current = list(initial_fidelities)

        for _ in range(steps):
            snapshot = [classify_qubit(max(0.0, f)) for f in current]
            trajectory.append(snapshot)
            current = [max(0.0, f - decay_rate) for f in current]

        return trajectory
