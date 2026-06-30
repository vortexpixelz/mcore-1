---
schema_id: D_cockpit
schema_version: 0.1
packet_version: 0.1
status: filled
source_bundle: Bundle 1
---

# Schema D: Cockpit Packet

## Destination

Validate `effective_alpha` as a calibrated Hölder regularity proxy against a
published turbulence DNS dataset (e.g., Johns Hopkins Turbulence Database).

## Current Position

NS-001 merged to main. The bijection between sigma and alpha is proven in the
unclamped region. The vorticity reduction model is implemented and clamped. No
real turbulence data has been used. The module is explicitly TOY DIAGNOSTIC.

## Signal

`sigma_2/sigma_0 = 0.5` — the register ratio is within the K41 Hölder range.
`effective_alpha` hits 0.0 at `omega_norm = 1.5` with default coupling weights.
Round-trip identity holds to machine precision for all register anchors.

## Uncertainty

- `lambda_omega = 0.5` and `eta_phase = 0.25` are uncalibrated — chosen by analogy.
- The additive reduction model has no PDE derivation.
- `sigma_2/sigma_0 = 0.5` proximity to K41 may be coincidence.
- DIANEW EVT protocol is untested on real neural data.

## Route

1. Identify one JHTDB DNS snapshot with known vorticity and structure-function exponents.
2. Extract `omega_norm` time series from the snapshot.
3. Run `effective_alpha` sweep over the extracted values.
4. Compare output trend to known Hölder exponents from the same snapshot.
5. If monotone decrease holds: upgrade conjecture to plausible; calibrate weights.
6. If not: falsify the additive model; record the failure in the claim-tier registry.

## Artifact

`experimental/ns001_gabor_holder.py` — the runnable diagnostic. CLI demo produces
the vorticity sweep table. All edge-case guards in place.

## Dismount

One GitHub issue scoped to step 1–4 above. No NS proof claim regardless of outcome.
