"""Tests for MethylationMetrics overlay (Domain 02 extension)."""

from __future__ import annotations

import pytest

from mcore_py.checker import check_tree
from mcore_py.model import Budget, Level, Tension, Trit
from mcore_py.overlays.methylation import (
    BETA_HEMIMETHYLATED_MAX,
    BETA_UNMETHYLATED_MAX,
    METHYLATION_HIERARCHY,
    MethylationMetrics,
    MethylationState,
    classify_cpg,
    cpg_cluster,
    cpg_island,
    cpg_site,
    cpg_weight,
)


# ---------------------------------------------------------------------------
# TestCpGClassification
# ---------------------------------------------------------------------------


class TestCpGClassification:
    def test_unmethylated_low(self):
        assert classify_cpg(0.00) == MethylationState.UNMETHYLATED

    def test_unmethylated_boundary(self):
        # beta just below threshold
        assert classify_cpg(BETA_UNMETHYLATED_MAX - 0.01) == MethylationState.UNMETHYLATED

    def test_hemimethylated_at_lower_boundary(self):
        assert classify_cpg(BETA_UNMETHYLATED_MAX) == MethylationState.HEMIMETHYLATED

    def test_hemimethylated_midpoint(self):
        assert classify_cpg(0.50) == MethylationState.HEMIMETHYLATED

    def test_hemimethylated_upper_boundary(self):
        assert classify_cpg(BETA_HEMIMETHYLATED_MAX - 0.01) == MethylationState.HEMIMETHYLATED

    def test_fully_methylated_at_boundary(self):
        assert classify_cpg(BETA_HEMIMETHYLATED_MAX) == MethylationState.FULLY_METHYLATED

    def test_fully_methylated_high(self):
        assert classify_cpg(1.00) == MethylationState.FULLY_METHYLATED

    def test_invalid_beta_negative(self):
        with pytest.raises(ValueError):
            classify_cpg(-0.01)

    def test_invalid_beta_over_one(self):
        with pytest.raises(ValueError):
            classify_cpg(1.01)

    def test_weight_ordering(self):
        """S1 < S2 < S3 must hold."""
        w_unmet = cpg_weight(MethylationState.UNMETHYLATED)
        w_hemi = cpg_weight(MethylationState.HEMIMETHYLATED)
        w_full = cpg_weight(MethylationState.FULLY_METHYLATED)
        assert w_unmet == Trit.S1
        assert w_hemi == Trit.S2
        assert w_full == Trit.S3


# ---------------------------------------------------------------------------
# TestCpGSite
# ---------------------------------------------------------------------------


class TestCpGSite:
    def test_unmethylated_site_weight(self):
        site = cpg_site(0.05)
        assert site.weight == Trit.S1

    def test_hemimethylated_site_weight(self):
        site = cpg_site(0.50)
        assert site.weight == Trit.S2

    def test_fully_methylated_site_weight(self):
        site = cpg_site(0.95)
        assert site.weight == Trit.S3

    def test_site_level(self):
        site = cpg_site(0.05)
        assert site.level == Level.L0_MATRA

    def test_site_label(self):
        site = cpg_site(0.10, label="cg00000029")
        assert site.label == "cg00000029"

    def test_site_features_beta(self):
        site = cpg_site(0.75)
        assert site.features["beta"] == pytest.approx(0.75)

    def test_site_features_state(self):
        site = cpg_site(0.75)
        assert site.features["methylation_state"] == "HEMIMETHYLATED"

    def test_site_tension_default(self):
        site = cpg_site(0.05)
        assert site.tension == Tension.NEUTRAL

    def test_site_tension_custom(self):
        site = cpg_site(0.95, tension=Tension.SURPLUS)
        assert site.tension == Tension.SURPLUS


# ---------------------------------------------------------------------------
# TestCpGCluster
# ---------------------------------------------------------------------------


class TestCpGCluster:
    def test_single_site_cluster(self):
        s = cpg_site(0.05)
        parent, children = cpg_cluster(s)
        assert parent.level == Level.L1_AKSARA
        assert parent.weight == Trit.S1
        assert len(children) == 1

    def test_two_site_cluster_sum(self):
        # S1 + S1 = S2 (trit addition: 0+0=0, but S1+S1... wait)
        # Actually: S1(weight=1 mora) + S1(weight=1 mora) = S2 (2 morae)
        # In the trit algebra: trit_add(S1, S1) = S2
        s1 = cpg_site(0.05)
        s2 = cpg_site(0.10)
        parent, children = cpg_cluster(s1, s2)
        assert parent.weight == Trit.S2
        assert len(children) == 2

    def test_cluster_label(self):
        s = cpg_site(0.05)
        parent, _ = cpg_cluster(s, label="island_cluster_1")
        assert parent.label == "island_cluster_1"

    def test_cluster_overflow_raises(self):
        # S2 + S2 overflows S3
        s1 = cpg_site(0.50)
        s2 = cpg_site(0.50)
        with pytest.raises(ValueError, match="overflow"):
            cpg_cluster(s1, s2)

    def test_s1_plus_s2_equals_s3(self):
        s1 = cpg_site(0.05)   # S1
        s2 = cpg_site(0.50)   # S2
        parent, _ = cpg_cluster(s1, s2)
        assert parent.weight == Trit.S3

    def test_cluster_feature_count(self):
        sites = [cpg_site(0.05), cpg_site(0.10), cpg_site(0.15)]
        parent, _ = cpg_cluster(*sites)
        assert parent.features["cpg_count"] == 3


# ---------------------------------------------------------------------------
# TestCpGIsland
# ---------------------------------------------------------------------------


class TestCpGIsland:
    def _make_cluster(self, beta: float, label: str = "c") -> tuple:
        s = cpg_site(beta, label=label)
        return cpg_cluster(s, label=f"cluster_{label}")

    def test_single_cluster_island(self):
        c = self._make_cluster(0.05)
        island = cpg_island(c)
        assert island.parent.level == Level.L2_GANA

    def test_island_check_tree_valid(self):
        c1 = self._make_cluster(0.05, "cg1")
        c2 = self._make_cluster(0.10, "cg2")
        island = cpg_island(c1, c2)
        result = check_tree(island)
        assert result.valid

    def test_island_label(self):
        c = self._make_cluster(0.05)
        island = cpg_island(c, label="BRCA1_promoter")
        assert island.parent.label == "BRCA1_promoter"

    def test_empty_island_raises(self):
        with pytest.raises(ValueError):
            cpg_island()

    def test_island_overflow_raises(self):
        # Two S3 clusters overflow
        s_full1 = cpg_site(0.95, label="cg1")
        s_full2 = cpg_site(0.95, label="cg2")
        c1 = cpg_cluster(s_full1, label="c1")
        c2 = cpg_cluster(s_full2, label="c2")
        with pytest.raises(ValueError, match="overflow"):
            cpg_island(c1, c2)

    def test_island_with_budget(self):
        c = self._make_cluster(0.05)
        budget = Budget(Trit.S1, Trit.S3)
        island = cpg_island(c, budget=budget)
        assert island.budget == budget


# ---------------------------------------------------------------------------
# TestMethylationMetrics
# ---------------------------------------------------------------------------


class TestMethylationMetrics:
    def test_site_shorthand(self):
        s = MethylationMetrics.site(0.05, label="cg1")
        assert s.weight == Trit.S1
        assert s.label == "cg1"

    def test_cluster_shorthand(self):
        s = MethylationMetrics.site(0.05)
        parent, children = MethylationMetrics.cluster(s)
        assert parent.level == Level.L1_AKSARA

    def test_island_shorthand(self):
        s = MethylationMetrics.site(0.05, label="cg1")
        c = MethylationMetrics.cluster(s, label="cluster_1")
        island = MethylationMetrics.island(c, label="TP53_promoter")
        assert island.parent.label == "TP53_promoter"

    def test_from_beta_list_single(self):
        island = MethylationMetrics.from_beta_list([0.05])
        result = check_tree(island)
        assert result.valid

    def test_from_beta_list_multiple(self):
        island = MethylationMetrics.from_beta_list(
            [0.05, 0.50],
            labels=["cg1", "cg2"],
            island_label="CDKN2A_promoter",
        )
        assert island.parent.label == "CDKN2A_promoter"
        result = check_tree(island)
        assert result.valid

    def test_from_beta_list_label_mismatch_raises(self):
        with pytest.raises(ValueError):
            MethylationMetrics.from_beta_list([0.05, 0.10], labels=["cg1"])

    def test_hierarchy_aliases(self):
        h = MethylationMetrics.HIERARCHY
        assert "island" in h.sanskrit(Level.L2_GANA).lower() or "island" in h.english(Level.L2_GANA).lower()


# ---------------------------------------------------------------------------
# TestEpigeneticDriftTrajectory
# ---------------------------------------------------------------------------


class TestEpigeneticDriftTrajectory:
    def test_step_count(self):
        traj = MethylationMetrics.decoherence_trajectory(
            [0.05, 0.10], steps=7
        )
        assert len(traj) == 7

    def test_qubit_count_per_step(self):
        traj = MethylationMetrics.decoherence_trajectory(
            [0.05, 0.10, 0.50], steps=3
        )
        for step in traj:
            assert len(step) == 3

    def test_hypermethylation_progression(self):
        # Start unmethylated, large drift -> should reach FULLY_METHYLATED
        traj = MethylationMetrics.decoherence_trajectory(
            [0.05], drift_rate=0.30, steps=10
        )
        initial = traj[0][0]
        final = traj[-1][0]
        assert initial == MethylationState.UNMETHYLATED
        assert final == MethylationState.FULLY_METHYLATED

    def test_hypomethylation_regression(self):
        # Start fully methylated, negative drift -> should reach UNMETHYLATED
        traj = MethylationMetrics.decoherence_trajectory(
            [0.95], drift_rate=-0.30, steps=10
        )
        initial = traj[0][0]
        final = traj[-1][0]
        assert initial == MethylationState.FULLY_METHYLATED
        assert final == MethylationState.UNMETHYLATED

    def test_clamping_at_zero(self):
        traj = MethylationMetrics.decoherence_trajectory(
            [0.05], drift_rate=-0.50, steps=5
        )
        for step in traj:
            assert step[0] == MethylationState.UNMETHYLATED

    def test_clamping_at_one(self):
        traj = MethylationMetrics.decoherence_trajectory(
            [0.95], drift_rate=0.50, steps=5
        )
        for step in traj:
            assert step[0] == MethylationState.FULLY_METHYLATED

    def test_monotonic_hypermethylation(self):
        # Positive drift should never decrease state value
        traj = MethylationMetrics.decoherence_trajectory(
            [0.10], drift_rate=0.10, steps=10
        )
        state_vals = [s[0].value for s in traj]
        assert all(
            state_vals[i] <= state_vals[i + 1]
            for i in range(len(state_vals) - 1)
        )


# ---------------------------------------------------------------------------
# TestMethylationHierarchyMap
# ---------------------------------------------------------------------------


class TestMethylationHierarchyMap:
    def test_l0_alias(self):
        skt = METHYLATION_HIERARCHY.sanskrit(Level.L0_MATRA)
        eng = METHYLATION_HIERARCHY.english(Level.L0_MATRA)
        assert "cpg" in skt.lower() or "cpg" in eng.lower()

    def test_l2_alias(self):
        eng = METHYLATION_HIERARCHY.english(Level.L2_GANA)
        assert "island" in eng.lower()

    def test_l4_alias(self):
        eng = METHYLATION_HIERARCHY.english(Level.L4_SLOKA)
        assert "locus" in eng.lower()


# ---------------------------------------------------------------------------
# TestOncologyScenarios — clinically motivated integration tests
# ---------------------------------------------------------------------------


class TestOncologyScenarios:
    def test_normal_promoter_valid(self):
        """Normal promoter: unmethylated CpGs -> check_tree valid."""
        island = MethylationMetrics.from_beta_list(
            [0.05, 0.10],
            island_label="TP53_normal",
        )
        assert check_tree(island).valid

    def test_tumor_suppressor_silencing_detected(self):
        """Aberrant hypermethylation of tumor suppressor -> overflow raises."""
        # Two fully-methylated clusters exceed S3 budget -> should raise
        s1 = MethylationMetrics.site(0.92, label="cg_tss_1")
        s2 = MethylationMetrics.site(0.95, label="cg_tss_2")
        c1 = MethylationMetrics.cluster(s1, label="cluster_1")
        c2 = MethylationMetrics.cluster(s2, label="cluster_2")
        with pytest.raises(ValueError, match="overflow|Overflow"):
            MethylationMetrics.island(c1, c2, label="CDKN2A_tumor")

    def test_hemimethylated_replication_state_valid(self):
        """Post-replication hemimethylated state -> check_tree valid."""
        island = MethylationMetrics.from_beta_list(
            [0.45],
            island_label="replication_fork",
        )
        assert check_tree(island).valid

    def test_cancer_progression_trajectory(self):
        """Drift from normal toward hypermethylation over 8 steps."""
        traj = MethylationMetrics.decoherence_trajectory(
            initial_betas=[0.08, 0.12, 0.10, 0.06],
            drift_rate=0.12,
            steps=8,
        )
        step_0_states = set(traj[0])
        step_7_states = set(traj[7])
        assert MethylationState.UNMETHYLATED in step_0_states
        assert MethylationState.FULLY_METHYLATED in step_7_states
