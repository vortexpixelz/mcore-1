"""
Formal tests for the Trit Prisoner's Dilemma Nash equilibrium claim.

Claim: the evolutionarily stable state of Trit PD is (0, 1/3, 2/3) on the N-D
edge — one third of the population remains undeclared. Binary PD has only (D,D).

Payoff matrix (same as mcore_game_sim.html):
    A[i][j] = payoff to strategy i when facing strategy j
    Strategies: C=0 (cooperate), N=1 (neutral/undeclared), D=2 (defect)
"""

import numpy as np
import pytest

# Payoff matrix from mcore_game_sim.html POP_A
A = np.array([
    [3.0, 1.5, -1.0],  # C vs {C, N, D}
    [1.5, 1.0,  0.5],  # N vs {C, N, D}
    [5.0, 2.0,  0.0],  # D vs {C, N, D}
])

NASH = np.array([0.0, 1.0 / 3.0, 2.0 / 3.0])  # claimed ESS


def _replicator(p: np.ndarray, A: np.ndarray) -> np.ndarray:
    Ap = A @ p
    mean = p @ Ap
    return p * (Ap - mean)


def _clamp(p: np.ndarray) -> np.ndarray:
    q = np.maximum(p, 0.0)
    s = q.sum()
    return q / s if s > 1e-12 else np.ones(3) / 3.0


def _rk4(p: np.ndarray, A: np.ndarray, dt: float) -> np.ndarray:
    k1 = _replicator(p, A)
    k2 = _replicator(_clamp(p + dt / 2 * k1), A)
    k3 = _replicator(_clamp(p + dt / 2 * k2), A)
    k4 = _replicator(_clamp(p + dt * k3), A)
    return _clamp(p + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4))


def _integrate(p0: np.ndarray, steps: int = 2000, dt: float = 0.04) -> np.ndarray:
    p = p0.copy()
    for _ in range(steps):
        p = _rk4(p, A, dt)
    return p


class TestNashFixedPoint:
    def test_nash_point_is_fixed(self):
        """(0, 1/3, 2/3) has zero replicator velocity."""
        dp = _replicator(NASH, A)
        assert np.allclose(dp, 0.0, atol=1e-10)

    def test_n_equals_d_fitness_at_nash(self):
        """f_N = f_D at the Nash point, verifying indifference condition."""
        Ap = A @ NASH
        assert abs(Ap[1] - Ap[2]) < 1e-12  # f_N == f_D

    def test_c_is_dominated_at_nash(self):
        """C receives strictly lower fitness than N and D at the Nash point."""
        Ap = A @ NASH
        assert Ap[0] < Ap[1]  # f_C < f_N
        assert Ap[0] < Ap[2]  # f_C < f_D


class TestNashStability:
    @pytest.mark.parametrize("p0", [
        [0.05, 0.30, 0.65],   # near Nash, slight C
        [0.10, 0.20, 0.70],   # moderate C, mostly D
        [0.01, 0.50, 0.49],   # very little C, N-heavy
        [0.33, 0.33, 0.34],   # near interior centre
        [0.20, 0.10, 0.70],   # high D, moderate C
    ])
    def test_converges_to_nash(self, p0):
        """Any interior trajectory converges to (0, 1/3, 2/3) within tolerance."""
        final = _integrate(np.array(p0, dtype=float))
        assert abs(final[0]) < 0.01, f"p_C={final[0]:.4f} didn't reach 0"
        assert abs(final[1] - 1 / 3) < 0.02, f"p_N={final[1]:.4f} didn't reach 1/3"
        assert abs(final[2] - 2 / 3) < 0.02, f"p_D={final[2]:.4f} didn't reach 2/3"

    def test_c_driven_to_zero(self):
        """C population always collapses regardless of starting share."""
        for p_c in [0.1, 0.3, 0.5, 0.7, 0.9]:
            rest = 1.0 - p_c
            p0 = np.array([p_c, rest / 2, rest / 2])
            final = _integrate(p0)
            assert final[0] < 0.01, f"p_C={final[0]:.4f} with p_c0={p_c}"

    def test_nd_edge_stays_on_nd_edge(self):
        """Trajectories starting on the N-D edge (p_C=0) stay there."""
        for t in [0.1, 0.3, 0.5, 0.7, 0.9]:
            p0 = np.array([0.0, t, 1.0 - t])
            final = _integrate(p0)
            assert final[0] < 1e-10, f"Left N-D edge: p_C={final[0]}"

    def test_nd_edge_converges_to_nash_ratio(self):
        """Any point on the N-D edge converges to (0, 1/3, 2/3)."""
        for t in [0.1, 0.3, 0.7, 0.9]:
            p0 = np.array([0.0, t, 1.0 - t])
            final = _integrate(p0)
            assert abs(final[1] - 1 / 3) < 0.01, f"p_N={final[1]:.4f} from t={t}"
            assert abs(final[2] - 2 / 3) < 0.01, f"p_D={final[2]:.4f} from t={t}"


class TestBinaryPD:
    def test_binary_pd_nash_is_all_defect(self):
        """On the C-D edge (p_N=0), all trajectories go to pure (D,D)."""
        for p_c in [0.1, 0.3, 0.5, 0.7, 0.9]:
            p0 = np.array([p_c, 0.0, 1.0 - p_c])
            final = _integrate(p0)
            assert final[2] > 0.99, f"Binary PD didn't reach D: p_D={final[2]:.4f}"

    def test_trit_ess_differs_from_binary_ess(self):
        """The trit ESS (1/3 neutral) is qualitatively different from binary (D,D)."""
        trit_final = _integrate(np.array([0.1, 0.3, 0.6]))
        binary_final = _integrate(np.array([0.5, 0.0, 0.5]))
        assert trit_final[1] > 0.3    # N persists in trit game
        assert binary_final[1] < 0.01  # N absent in binary game
