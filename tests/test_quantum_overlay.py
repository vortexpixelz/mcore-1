"""
Tests for QuantumResourceMetrics overlay (MCORE-Q).

Validates the isomorphism between quantum OS resource scheduling and
MCORE-1 ternary conservation: the same check_tree() that validates a
Sanskrit metrical foot validates a quantum scheduling frame.
"""

import pytest

from mcore_py.model import Budget, Level, Tension, Trit
from mcore_py.checker import check_tree, ErrorKind
from mcore_py.overlays.quantum import (
    FIDELITY_IDLE_MAX,
    FIDELITY_OPERATIONAL_MAX,
    QUBIT_WEIGHT_MAP,
    QUANTUM_HIERARCHY,
    QubitState,
    QuantumResourceMetrics,
    classify_qubit,
    qubit_slot,
    qubit_weight,
    scheduling_frame,
    task_slot,
)


# ===================================================================
# Qubit classification
# ===================================================================

class TestQubitClassification:

    def test_idle_below_threshold(self):
        assert classify_qubit(0.00) == QubitState.IDLE
        assert classify_qubit(0.69) == QubitState.IDLE

    def test_operational_range(self):
        assert classify_qubit(0.70) == QubitState.OPERATIONAL
        assert classify_qubit(0.89) == QubitState.OPERATIONAL

    def test_entangled_at_and_above_threshold(self):
        assert classify_qubit(0.90) == QubitState.ENTANGLED
        assert classify_qubit(1.00) == QubitState.ENTANGLED

    def test_invalid_fidelity_negative(self):
        with pytest.raises(ValueError):
            classify_qubit(-0.01)

    def test_invalid_fidelity_above_one(self):
        with pytest.raises(ValueError):
            classify_qubit(1.01)

    def test_weight_map_covers_all_states(self):
        for state in QubitState:
            assert state in QUBIT_WEIGHT_MAP

    def test_weight_ordering_matches_trit_ordering(self):
        assert qubit_weight(QubitState.IDLE)        == Trit.S1
        assert qubit_weight(QubitState.OPERATIONAL) == Trit.S2
        assert qubit_weight(QubitState.ENTANGLED)   == Trit.S3


# ===================================================================
# Qubit slot construction
# ===================================================================

class TestQubitSlot:

    def test_idle_qubit_weight_and_level(self):
        q = qubit_slot(0.50, label="q0")
        assert q.weight == Trit.S1
        assert q.level  == Level.L0_MATRA
        assert q.label  == "q0"

    def test_operational_qubit(self):
        q = qubit_slot(0.80)
        assert q.weight == Trit.S2
        assert q.features["qubit_state"] == "OPERATIONAL"

    def test_entangled_qubit(self):
        q = qubit_slot(0.95)
        assert q.weight == Trit.S3
        assert q.features["qubit_state"] == "ENTANGLED"

    def test_fidelity_stored_in_features(self):
        q = qubit_slot(0.85, label="q3")
        assert q.features["fidelity"] == 0.85

    def test_tension_propagated(self):
        q = qubit_slot(0.80, tension=Tension.DEBT)
        assert q.tension == Tension.DEBT


# ===================================================================
# Task slot construction
# ===================================================================

class TestTaskSlot:

    def test_single_qubit_task(self):
        q = qubit_slot(0.80)
        parent, children = task_slot(q, label="H_q0")
        assert parent.weight == Trit.S2
        assert parent.level  == Level.L1_AKSARA
        assert parent.label  == "H_q0"
        assert children == [q]

    def test_two_qubit_task_idle_plus_operational(self):
        # S1 + S2 = S3 — valid
        q0 = qubit_slot(0.50)  # IDLE = S1
        q1 = qubit_slot(0.80)  # OPERATIONAL = S2
        parent, children = task_slot(q0, q1, label="CNOT")
        assert parent.weight == Trit.S3
        assert len(children) == 2

    def test_two_qubit_task_overflow_raises(self):
        # S2 + S2 = OVERFLOW
        q0 = qubit_slot(0.80)
        q1 = qubit_slot(0.80)
        with pytest.raises(ValueError, match="overflow"):
            task_slot(q0, q1)

    def test_qubit_count_stored_in_features(self):
        q = qubit_slot(0.80)
        parent, _ = task_slot(q)
        assert parent.features["task_qubit_count"] == 1


# ===================================================================
# Scheduling frame construction and check_tree validation
# ===================================================================

class TestSchedulingFrame:

    def _frame_s1_s2(self):
        """Helper: frame with one IDLE task (S1) and one OPERATIONAL task (S2)."""
        t0 = task_slot(qubit_slot(0.50), label="task0")  # S1
        t1 = task_slot(qubit_slot(0.80), label="task1")  # S2
        return scheduling_frame(t0, t1)

    def test_frame_is_constituent(self):
        from mcore_py.model import Constituent
        assert isinstance(self._frame_s1_s2(), Constituent)

    def test_frame_level_is_gana(self):
        assert self._frame_s1_s2().parent.level == Level.L2_GANA

    def test_frame_weight_conservation(self):
        # S1 + S2 = S3
        assert self._frame_s1_s2().parent.weight == Trit.S3

    def test_frame_passes_check_tree(self):
        result = check_tree(self._frame_s1_s2())
        assert result.valid

    def test_empty_frame_raises(self):
        with pytest.raises(ValueError):
            scheduling_frame()

    def test_frame_overflow_raises(self):
        # S2 + S2 = OVERFLOW
        t0 = task_slot(qubit_slot(0.80))
        t1 = task_slot(qubit_slot(0.80))
        with pytest.raises(ValueError, match="overflow"):
            scheduling_frame(t0, t1)

    def test_frame_with_budget_satisfied(self):
        budget = Budget(min_weight=Trit.S1, max_weight=Trit.S3)
        frame = scheduling_frame(
            task_slot(qubit_slot(0.50)),
            task_slot(qubit_slot(0.80)),
            budget=budget,
        )
        assert check_tree(frame).valid

    def test_frame_with_budget_violation(self):
        # Budget allows only S1-weight total (value=0), frame has S1+S2 (value=1)
        budget = Budget(min_weight=Trit.S1, max_weight=Trit.S1, exact=True)
        frame = scheduling_frame(
            task_slot(qubit_slot(0.50)),
            task_slot(qubit_slot(0.80)),
            budget=budget,
        )
        result = check_tree(frame)
        assert not result.valid
        assert any(e.kind == ErrorKind.BUDGET for e in result.errors)


# ===================================================================
# QuantumResourceMetrics high-level interface
# ===================================================================

class TestQuantumResourceMetrics:

    def test_qubit_shorthand(self):
        q = QuantumResourceMetrics.qubit(0.95, label="q0")
        assert q.weight == Trit.S3

    def test_task_shorthand(self):
        q = QuantumResourceMetrics.qubit(0.80)
        parent, _ = QuantumResourceMetrics.task(q, label="H")
        assert parent.weight == Trit.S2

    def test_frame_shorthand_valid(self):
        t = QuantumResourceMetrics.task(QuantumResourceMetrics.qubit(0.80))
        result = check_tree(QuantumResourceMetrics.frame(t))
        assert result.valid

    def test_from_fidelity_list_single_entangled(self):
        frame = QuantumResourceMetrics.from_fidelity_list([0.95])
        assert frame.parent.weight == Trit.S3
        assert check_tree(frame).valid

    def test_from_fidelity_list_idle_plus_operational(self):
        # S1 (0.50) + S2 (0.80) = S3 frame
        frame = QuantumResourceMetrics.from_fidelity_list([0.50, 0.80], labels=["q0", "q1"])
        assert frame.parent.weight == Trit.S3
        assert check_tree(frame).valid

    def test_from_fidelity_list_label_mismatch_raises(self):
        with pytest.raises(ValueError, match="labels length"):
            QuantumResourceMetrics.from_fidelity_list([0.80, 0.50], labels=["q0"])

    def test_from_fidelity_list_overflow_raises(self):
        # Two OPERATIONAL tasks: S2 + S2 = OVERFLOW
        with pytest.raises(ValueError):
            QuantumResourceMetrics.from_fidelity_list([0.80, 0.80])

    def test_from_fidelity_list_auto_labels(self):
        frame = QuantumResourceMetrics.from_fidelity_list([0.95])
        child_qubit = frame.children[0].children[0]
        assert child_qubit.label == "q0"


# ===================================================================
# Decoherence trajectory
# ===================================================================

class TestDecoherenceTrajectory:

    def test_trajectory_step_count(self):
        traj = QuantumResourceMetrics.decoherence_trajectory([0.95, 0.80], steps=4)
        assert len(traj) == 4

    def test_trajectory_per_qubit_count(self):
        traj = QuantumResourceMetrics.decoherence_trajectory([0.95, 0.80, 0.50], steps=3)
        assert all(len(step) == 3 for step in traj)

    def test_trajectory_degrades_across_trit_boundaries(self):
        # 0.95 (ENTANGLED) decays by 0.30 per step -> 0.65 (IDLE) at step 1
        traj = QuantumResourceMetrics.decoherence_trajectory([0.95], decay_rate=0.30, steps=4)
        assert traj[0][0] == QubitState.ENTANGLED
        assert traj[1][0] == QubitState.IDLE

    def test_trajectory_clamps_at_zero(self):
        traj = QuantumResourceMetrics.decoherence_trajectory([0.10], decay_rate=0.20, steps=5)
        # After step 0 (0.10 -> IDLE), fidelity hits zero and stays there
        assert all(step[0] == QubitState.IDLE for step in traj[1:])

    def test_trajectory_default_steps_is_five(self):
        traj = QuantumResourceMetrics.decoherence_trajectory([0.90])
        assert len(traj) == 5


# ===================================================================
# Quantum hierarchy map
# ===================================================================

class TestQuantumHierarchyMap:

    def test_quantum_aliases_by_level(self):
        hm = QUANTUM_HIERARCHY
        assert hm.sanskrit(Level.L0_MATRA) == "qubit_slot"
        assert hm.sanskrit(Level.L1_AKSARA) == "task_slot"
        assert hm.sanskrit(Level.L2_GANA)  == "scheduling_frame"
        assert hm.sanskrit(Level.L3_PADA)  == "circuit_layer"
        assert hm.sanskrit(Level.L4_SLOKA) == "circuit"

    def test_english_aliases(self):
        hm = QUANTUM_HIERARCHY
        assert hm.english(Level.L2_GANA)  == "scheduling frame"
        assert hm.english(Level.L4_SLOKA) == "circuit"

    def test_lookup_by_quantum_name(self):
        hm = QUANTUM_HIERARCHY
        assert hm.from_name("scheduling_frame") == Level.L2_GANA
        assert hm.from_name("circuit")          == Level.L4_SLOKA
        assert hm.from_name("task_slot")        == Level.L1_AKSARA
