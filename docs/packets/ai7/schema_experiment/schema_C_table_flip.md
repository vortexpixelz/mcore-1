---
schema_id: C_table_flip
schema_version: 0.1
packet_version: 0.1
status: filled
source_bundle: Bundle 1
---

# Schema C: Table Flip Packet

## Receipt

NS-001 Gabor-Hölder toy diagnostic merged to main (PR #35, June 2026).
Module: `experimental/ns001_gabor_holder.py`. Five Copilot review rounds addressed.
Round-trip identity verified. DIANEW Study A EVT protocol added in same pull.

## Claim

The MCORE-1 sigma register, originally designed for audio, contains a latent
Hölder regularity structure that can be extracted deterministically and used as a
falsification target for NS blow-up proxy models.

## Ledger

### Observed

- `holder_alpha_from_sigma` and `sigma_from_holder` are exact inverses in the
  unclamped region (`depth > 0`, `alpha ∈ (0,1)`).
- `sigma_2/sigma_0 = 0.5` (measured from production files).
- `effective_alpha` clamps to `[0,1]`; floor reached at `omega_norm = 1.5`.
- 273 core tests pass; 5 DIANEW EVT tests pass.

### Plausible

- `sigma_2/sigma_0 = 0.5` may be calibratable against K41 (exponent ~1/3).
- The additive vorticity reduction model qualitatively tracks regularity loss.

### Speculative

- Rising `alpha_eff → 0` might serve as a blow-up early-warning signal in
  synthetic turbulence fields.

### Forbidden for now

- NS-001 solves Navier-Stokes. Proof of global regularity. Exact K41 measurement
  before experimental validation against real turbulence data.

## Sentence

The sigma register is a signal-processing artifact that accidentally encodes a
falsifiable regularity proxy — and that accident is worth testing.

## Ask

One DNS calibration run to determine whether `effective_alpha` tracks known Hölder
exponents in published synthetic turbulence data.
