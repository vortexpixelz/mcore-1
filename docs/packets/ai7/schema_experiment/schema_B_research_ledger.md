---
schema_id: B_research_ledger
schema_version: 0.1
packet_version: 0.1
status: filled
source_bundle: Bundle 1
---

# Schema B: Research Ledger Packet

## Observation

The MCORE-1 production Gabor sigma register uses three depth-indexed values
(0.002 → 0.0015 → 0.001). The ratio between consecutive levels is constant at 0.75,
and the overall ratio `sigma_2/sigma_0 = 0.5`. These values were chosen for audio
synthesis; they were not derived from fluid dynamics.

## Interpretation

The cascade model `sigma_d = sigma_0 · 2^(-alpha · depth)` inverts cleanly to a
Hölder regularity exponent. The register's depth-3 structure mirrors a three-level
Richardson energy cascade structurally. The `sigma_2/sigma_0 = 0.5` ratio happens
to neighbour the K41 Hölder range (1/3, 1), which may be coincidence or may indicate
the audio compression heuristics share a root with turbulence scaling.

## Hypothesis

`alpha_eff = alpha_0 - lambda_omega · omega_norm - eta_phase · |theta_jump| / pi`
tracks qualitative Hölder regularity loss under rising vorticity in synthetic fields,
and could be calibrated as a falsification target against published DNS data.

## Evidence Receipts

- `holder_alpha_from_sigma(0.0015, 0.002, 1)` → `alpha ≈ 0.415` (depth-1 register value)
- `holder_alpha_from_sigma(0.001, 0.002, 2)` → `alpha = 0.5` (depth-2 register value)
- Round-trip identity verified to `< 1e-12` for both register points
- `sigma_2/sigma_0 = 0.5`; K41 predicts Hölder exponent `~1/3` in inertial range
- `effective_alpha` clamps correctly; `alpha_eff = 0.0` at `omega_norm = 1.5` with
  `lambda_omega = 0.5`, `alpha_0 = 0.75`
- 273 core tests passing; NS-001 module validated via CLI round-trip

## Falsification Test

Run `effective_alpha` against the Johns Hopkins Turbulence Database vorticity field.
If `alpha_eff` does not monotonically decrease as vorticity increases near dissipation
scales, the additive reduction model is falsified and the conjecture is dropped.

## Next Action

Open a GitHub issue to define the JHTDB calibration experiment: pick one DNS snapshot,
extract `omega_norm` time series, run `effective_alpha` sweep, compare to known
structure-function scaling exponents from the same snapshot.
