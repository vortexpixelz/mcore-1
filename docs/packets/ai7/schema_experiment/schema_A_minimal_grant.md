---
schema_id: A_minimal_grant
schema_version: 0.1
packet_version: 0.1
status: filled
source_bundle: Bundle 1
---

# Schema A: Minimal Grant Packet

## Claim

A depth-aware Gabor sigma register can be mapped bijectively to a Hölder regularity
exponent via a deterministic cascade model, providing a falsifiable diagnostic proxy
for turbulence regularity without requiring a Navier-Stokes solution.

## Problem

Hölder regularity exponents for NS solutions are theoretically bounded but
experimentally inaccessible in real flows. A purely signal-processing proxy — if
well-calibrated — could serve as a benchmark target for synthetic turbulence datasets.

## Evidence

- Round-trip identity: `sigma_from_holder(holder_alpha_from_sigma(σ, σ₀, d), σ₀, d) = σ`
  holds to machine precision for all register anchors in the unclamped region.
- `sigma_2/sigma_0 = 0.5` sits within the K41 Hölder range (1/3, 1).
- Vorticity sweep shows monotone `alpha_eff` reduction to 0 at `omega_norm = 1.5`.
- 273 passing tests validate the underlying ternary weight algebra.

## Experiment

Run `effective_alpha` against a published synthetic turbulence vorticity field
(e.g., Johns Hopkins Turbulence Database). If `alpha_eff` tracks the known Hölder
exponent trend, the calibration is plausible. If it does not, the model is falsified.

## Ask

Compute time on a turbulence DNS dataset for one calibration run of `effective_alpha`
against known vorticity profiles.
