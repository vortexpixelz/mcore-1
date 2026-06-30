---
packet_id: AI7-BUNDLE-1-SOURCE
schema_version: 0.1
packet_version: 0.1
status: filled
source_bundle: Bundle 1
date_created: 2026-06-23
---

# Source Bundle Notes

## Raw source inventory

MCORE-1 experimental lane — work completed June 2026.

- `experimental/ns001_gabor_holder.py` — NS-001 Gabor-Hölder toy diagnostic module
- `docs/badabing/NS001_GABOR_HOLDER_VORTICITY_PACKET.md` — claim-tier registry for NS-001
- `experimental/dianew_evt_study_a.py` — DIANEW Study A EVT declustering protocol
- `docs/badabing/DIANEW_STUDY_A_PROTOCOL.md` — protocol spec
- `experimental/schema_factory/` — schema selection scaffold (this experiment)
- `tests/` — 278 passing tests, 71% coverage of `src/mcore_py/`

## Receipts

- NS-001: `holder_alpha_from_sigma` and `sigma_from_holder` are exact inverses for
  `depth > 0`, `alpha ∈ (0, 1)` (the unclamped region). Verified by round-trip test
  in CLI demo: `sigma_back` matches to `< 1e-12` for all three register anchors.
- Sigma register anchors confirmed in production files: `sigma_0=0.002` (depth 0),
  `sigma_1=0.0015` (depth 1), `sigma_2=0.001` (depth 2). Ratio `sigma_2/sigma_0 = 0.5`.
- `effective_alpha` clamps to `[0, 1]`; at `omega_norm=1.5`, `alpha_eff` hits 0.0 (floor).
- DIANEW Study A: EVT declustering retains one maximum per cluster; GPD fit produces
  finite conditional endpoint for negative shape; 5 tests passing.
- 273 tests passing pre-pull; 278 passing post-pull (DIANEW added 5).
- Schema factory test: red → green cycle completed in this session.

## Claims already present in the bundle

- [ESTABLISHED] The sigma→alpha and alpha→sigma functions are exact inverses in the
  unclamped region. No PDE claim attached.
- [PLAUSIBLE] `sigma_2/sigma_0 = 0.5` numerically neighbours the K41 Hölder range
  (1/3, 1); could serve as calibration target against synthetic turbulence benchmarks.
- [ANALOGY] Three-level sigma cascade mirrors Richardson energy cascade structurally.
- [CONJECTURE] Vorticity-adjusted `alpha_eff → 0` may signal approach to a singularity
  regime in synthetic fields; unvalidated against real turbulence data.
- [CONJECTURE] EVT declustering on neural spike trains may separate signal from
  extreme-noise events; unvalidated on real neural data.

## Open questions

- Does `sigma_2/sigma_0 = 0.5` survive contact with a synthetic K41 benchmark?
- What is the right `lambda_omega` / `eta_phase` calibration for real vorticity data?
- Can DIANEW Study A be validated against a published EVT neuroscience dataset?
- Should the schema factory produce typed schemas (Pydantic) or stay YAML-only?

## Possible AI7 / NSF fit

- NS-001 is a falsification target: if `alpha_eff` stays bounded away from 0 under
  real turbulence vorticity, the conjecture is falsified — that is useful science.
- DIANEW EVT protocol is designed as a pre-processing step for neural spike analysis;
  could fit a neuroscience data-infrastructure grant.
- The ternary weight algebra (273 tests, proven cascade theorems) is the stable core
  that makes both overlays credible.

## Notes that should not become claims yet

- The NS-001 module is explicitly TOY DIAGNOSTIC — NOT PROOF-BEARING.
- No NS solution claim. No global regularity claim. No exact K41 measurement.
- DIANEW Study A is a protocol scaffold; the EVT fit has not been run on real data.
