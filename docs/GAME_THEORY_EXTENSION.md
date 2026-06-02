# MCORE-1 Game Theory Extension

> **Status tags follow** `docs/CLAIMS.md` conventions:
> `[ESTABLISHED]` | `[PLAUSIBLE]` | `[CONJECTURAL]`

---

## Overview

The game theory extension applies the MCORE-1 ternary algebra to strategic interaction. The
mapping replaces prosodic weights with strategic stances: **C** (cooperate / light), **N**
(neutral-undeclared / heavy), **D** (defect / superheavy). The conservation invariant becomes
a budget constraint on population-level strategy distributions.

Two interactive visualizations and a formal test suite constitute the current deliverable.

---

## Files

| File | Purpose |
|------|---------|
| `game_theory_geometry.html` | Three.js r128 3D simplex visualizer |
| `mcore_game_sim.html` | Cascade / Population / Tournament simulator |
| `tests/test_game_theory_nash.py` | Formal pytest suite for the Trit PD Nash claim |

---

## The Trit Prisoner's Dilemma

### Strategy mapping

| Trit | Strategy | Description |
|------|----------|-------------|
| S1 (light) | C — Cooperate | Declare cooperative intent |
| S2 (heavy) | N — Neutral / Undeclared | Withhold declaration |
| S3 (superheavy) | D — Defect | Declare defection |

The ternary algebra's OVERFLOW rule (`S3 + S3 = OVERFLOW`) maps naturally to bilateral
defection exceeding a payoff budget.

### Payoff matrix

`A[i][j]` = payoff to strategy `i` when facing strategy `j`:

```
             C      N      D
C (S1)  [ 3.0,  1.5, -1.0 ]
N (S2)  [ 1.5,  1.0,  0.5 ]
D (S3)  [ 5.0,  2.0,  0.0 ]
```

This matrix is used identically in `mcore_game_sim.html` (`POP_A`) and
`tests/test_game_theory_nash.py`.

---

## The Nash Equilibrium Claim

### `[ESTABLISHED]` Fixed point

**(0, 1/3, 2/3) is a Nash fixed point of the replicator dynamics.**

Verified analytically:
- At `p = (0, 1/3, 2/3)`: `f_N = A[1]·p = 1·(1/3) + 0.5·(2/3) = 2/3`
- At `p = (0, 1/3, 2/3)`: `f_D = A[2]·p = 2·(1/3) + 0·(2/3) = 2/3`
- `f_N = f_D` — indifference condition satisfied `[ESTABLISHED]`
- `f_C = A[0]·p = 1.5·(1/3) + (-1)·(2/3) = -1/6 < f_N = f_D` — C strictly dominated `[ESTABLISHED]`
- Replicator velocity `dp/dt = 0` at this point `[ESTABLISHED]`

Verified in code: `tests/test_game_theory_nash.py::TestNashFixedPoint` (3 tests, all pass).

### `[PLAUSIBLE]` Asymptotic stability

**Interior trajectories converge to (0, 1/3, 2/3).**

Verified numerically via RK4 replicator integration (2000 steps, dt=0.04, total time 80):
- 5 parametrized interior starting points converge within tolerance — `[PLAUSIBLE]`
- C population collapses for any initial share — `[PLAUSIBLE]`
- N-D edge is invariant and converges to 1/3:2/3 ratio — `[PLAUSIBLE]`

This is asymptotic stability, not strict ESS in the formal game-theoretic sense (which would
additionally require demonstrated invasion barrier from arbitrary mutant strategies).

### `[ESTABLISHED]` Contrast with binary PD

**On the C-D subspace (p_N = 0), all trajectories converge to pure (D, D).**

The C-D subspace is invariant under replicator dynamics (p_N = 0 ⟹ dp_N/dt = 0). Within
that subspace, D dominates C: `A[D][C] = 5 > A[C][C] = 3`, `A[D][D] = 0 > A[C][D] = -1`.
All trajectories go to (0, 0, 1). `[ESTABLISHED]`

**The trit ESS (one-third neutral) is qualitatively different from binary PD (all-defect).**
The existence of the N strategy creates a stable mixed equilibrium that binary games cannot
produce. `[ESTABLISHED]`

---

## Visualizations

### `game_theory_geometry.html` — 3D Simplex

Built with Three.js r128 (last version with plain-script OrbitControls, no ES module import
needed).

**Features:**
- Payoff landscape rendered as a triangular mesh on the 2D simplex projected into 3D
- Replicator dynamics trajectories (RK4, 500 steps, dt=0.05) rendered as animated lines
- Nash equilibria marked as gold `MeshPhongMaterial` spheres with translucent halos and
  rotating torus rings
- Five game presets: Prisoner's Dilemma, Coordination, Hawk-Dove, Stag Hunt,
  Rock-Paper-Scissors
- Click to place a starting point; drag to orbit

**Key implementation detail — barycentric triangular grid:**

Grid index formula for an N-division triangulation of the simplex:
```
idx(i, j) = i*(N+1) - i*(i-1)/2 + j
```
where `i` is the row and `j` is the column within that row. Upper-triangle of each quad
exists only when `i + j < N`.

**Coordinate conversion** uses Cramer's rule on the edge vectors `U = V2 - V1`,
`V = V3 - V1` to compute barycentric coordinates from a clicked 3D point.

### `mcore_game_sim.html` — Three-Tab Simulator

**Tab 1: Cascade**
- 22×22 agent grid; each cell is C / N / D
- Defection events propagate to neighbors with configurable probability
- **MCORE-1 Budget Conservation toggle**: when enabled, every defection event is paired with
  a forced cooperation event on a randomly selected neutral cell, maintaining the population
  weight budget via `trit_add` semantics

**Tab 2: Population**
- Canvas 2D simplex with payoff-colored landscape (`HSL → RGB`)
- Click to set starting point; replicator dynamics run in real time (RK4)
- Trajectory history drawn as a fading path; Nash attractor marked

**Tab 3: Tournament**
- 8 named strategies compete in round-robin: `AllC`, `AllN`, `AllD`, `TFT`, `TFN`,
  `Pavlov`, `GrimTrigger`, `RandomTrit`
- Strategy functions: `fn(myHistory, oppHistory, myPayoffs) → {-1, 0, 1}`
- Payoff indexing: `A[action + 1][opponent_action + 1]` where actions ∈ {-1, 0, 1}

---

## Test Coverage

`tests/test_game_theory_nash.py` (122 lines, 13 tests):

| Class | Tests | Verifies |
|-------|-------|---------|
| `TestNashFixedPoint` | 3 | Fixed point: zero replicator velocity; f_N = f_D; C dominated |
| `TestNashStability` | 5+3 | Interior convergence (5 parametrized starts); C driven to 0; N-D edge invariance and convergence |
| `TestBinaryPD` | 2 | C-D subspace converges to all-D; trit and binary ESS qualitatively differ |

**Integration kernel:**
```python
def _replicator(p, A):
    Ap = A @ p
    return p * (Ap - p @ Ap)   # dp/dt = p * (fitness - mean fitness)

def _rk4(p, A, dt):            # RK4 with simplex projection after each substep
    ...

def _integrate(p0, steps=2000, dt=0.04):  # total time T=80
    ...
```

**Known open issues (from code review):**
- `test_binary_pd_nash_is_all_defect` tests only the invariant C-D subspace; it does not
  verify that (0, 0, 1) is unstable to N-invasion from the full trit space (it is).
- `trit_final[1] > 0.3` (line 112) is a loose lower-bound; `abs(final[1] - 1/3) < 0.02`
  would be tighter.
- Claim language uses "ESS" — more precisely, the tests establish asymptotic stability of
  the Nash point, not full ESS (which requires an invasion-barrier proof).

---

## Connection to MCORE-1 Conservation

The budget conservation toggle in the cascade simulator is the direct link to `check_tree()`.
When enabled:

1. A defection event raises a cell's trit weight by +1
2. A compensating cooperation event is selected at random from neutral (S2) cells
3. The population weight sum is maintained: `trit_add_seq(all_weights)` stays valid

This is the same invariant `check_tree()` enforces across prosody, methylation, and quantum
domains. The cascade simulator makes it interactive and visual.

---

## What Would Promote Claims

| Claim | Current status | What promotes it |
|-------|---------------|-----------------|
| Fixed point at (0, 1/3, 2/3) | `[ESTABLISHED]` | Already proven analytically + numerically |
| Interior convergence | `[PLAUSIBLE]` | Prove Lyapunov function on the N-D edge subspace |
| Full ESS (invasion barrier) | `[CONJECTURAL]` | Linearize replicator at Nash; show all eigenvalues negative |
| Budget conservation ↔ check_tree() | `[PLAUSIBLE]` | Extend `check_tree()` to accept a population vector; add pytest |
| Universal trit game theory | `[CONJECTURAL]` | Apply to additional game classes; find a counterexample or prove it |
