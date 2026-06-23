# NS-001 Gabor-Hölder Vorticity Packet

**Status:** EXPERIMENTAL — TOY DIAGNOSTIC ONLY
**Module:** `experimental/ns001_gabor_holder.py`
**Branch:** `research/ns-toy-model`
**Parent issue:** #27 (NS-001 writeup)
**Implementation issue:** #28

---

## Claim Tier Registry

All claims made by or associated with this module are classified below.
This registry is the authoritative record for review safety.

---

### ESTABLISHED

Claims that are mathematically or empirically settled within the scope
of the module itself; no external PDE or physics validation required.

| # | Claim | Basis |
|---|-------|-------|
| E1 | `holder_alpha_from_sigma(sigma_d, sigma_0, depth)` and `sigma_from_holder(sigma_0, alpha, depth)` form a deterministic, invertible bijection for `depth > 0` and `sigma_d < sigma_0`. | Algebraic identity: `log2(sigma_0/sigma_d)/depth` inverts `sigma_0 * 2^(-alpha*depth)`. Round-trip error < 1e-12 (float64). |
| E2 | `effective_alpha` is a pure arithmetic function; given identical inputs it always returns identical output. | No state, no randomness. |
| E3 | The sigma register `{0: 0.002, 1: 0.0015, 2: 0.001}` is identical to `SONI_PARAMS` in `solar_ingestor.py` and `_DEPTH_PARAMS` in `astro_mcore_ingestor.py`. | Direct code comparison confirms field-by-field match. |
| E4 | The alpha band produced by `sigma_band()` is `{depth=0: alpha=1.0, depth=1: alpha≈0.415, depth=2: alpha=0.5}` for the canonical register. | Deterministic closed-form evaluation. |

---

### PLAUSIBLE

Claims that are physically or mathematically reasonable but lack formal
proof or cross-domain empirical validation.

| # | Claim | Basis | Validation path |
|---|-------|-------|----------------|
| P1 | The sigma ratio `sigma_2 / sigma_0 = 0.5` numerically neighbours the Kolmogorov–Obukhov–She–Lévêque Hölder exponent range `(1/3, 1)` for turbulent velocity increments. | K41 predicts `alpha ≈ 1/3`; intermittency corrections push it toward 0.37–0.40. `sigma_from_holder(0.002, 1/3, 2) ≈ 0.00126`, which is in the sub-register range. | Benchmark against synthetic turbulence fields (e.g., forced Burgers or 3-D pseudospectral NS at Re~1000). |
| P2 | Rising normalised vorticity is a qualitative proxy for decreasing local regularity in the velocity field. | Consistent with Beale–Kato–Majda criterion: blow-up requires `∫‖ω‖_∞ dt → ∞`. | Requires actual NS solver output; not provided by this module. |
| P3 | Phase discontinuities at Gabor depth boundaries correspond qualitatively to wavelet coefficient irregularities used in Hölder exponent estimation. | Wavelet modulus maxima methods (Mallat–Hwang 1992) use log-linear scaling of coefficients vs. scale to estimate pointwise Hölder exponents. | Implement wavelet-based Hölder estimator and compare output to `holder_alpha_from_sigma`. |

---

### ANALOGY

Structural or conceptual parallels that motivate the module design but
do not constitute evidence for the associated physical claims.

| # | Analogy | Holds because | Does NOT imply |
|---|---------|--------------|----------------|
| A1 | The three-level sigma cascade `0.002 → 0.0015 → 0.001` mirrors a Richardson energy cascade `L → L/r → L/r²`. | Both are geometric sequences with ratio < 1. | The sigma levels correspond to physical length or time scales without external calibration. |
| A2 | Gabor sigma decreasing with depth (at fixed alpha) is structurally analogous to wavelet coefficient decay across scales in Hölder estimation. | Both involve a scale parameter that shrinks at finer cascade levels; `sigma_d = sigma_0 * 2^(-alpha * depth)` is strictly decreasing in depth for alpha > 0. | The Gabor atom is a physically faithful model of turbulent eddy structure. |
| A3 | The MCORE-1 trit cascade (S1→S2→S3) maps to a vorticity hierarchy by depth index. | Both have three levels with decreasing amplitude/sigma. | Trits encode vorticity values or any fluid-mechanical quantity. |

---

### CONJECTURE

Unvalidated hypotheses that the module exposes as falsification targets.

| # | Conjecture | Falsification target |
|---|-----------|---------------------|
| C1 | `effective_alpha → 0` as `omega_norm → alpha_0 / lambda_omega` corresponds to onset of a blow-up proxy in the toy cascade. | Generate synthetic 1-D Burgers blow-up; measure pointwise Hölder exponents; compare to `effective_alpha` at equivalent normalised vorticity. |
| C2 | `sigma_from_holder(sigma_0, effective_alpha(...), depth)` produces a sigma register that, when fed back into the audio synthesis pipeline, generates a qualitatively distinct acoustic texture before and after the blow-up proxy threshold. | A/B listening test on audio produced at `alpha_eff > 0.3` vs. `alpha_eff < 0.1`. |
| C3 | Phase jump `theta_jump = pi` at depth boundary is a proxy for a vortex sheet discontinuity, and the associated `eta_phase = 0.25` weight is calibratable from real vortex sheet data. | Simulate Kelvin–Helmholtz roll-up; measure phase coherence of Gabor coefficients across the sheet; fit `eta_phase`. |

---

### FORBIDDEN PUBLIC CLAIM

The following statements **must never appear** in any public-facing
communication, paper draft, blog post, or social media referencing this
module or the MCORE-1 project.

| Forbidden statement | Why |
|--------------------|-----|
| "MCORE-1 solves Navier-Stokes" | No proof of global regularity has been constructed. The module is a toy diagnostic. |
| "Proof of global regularity for 3-D NS" | This is an open Clay Millennium Prize problem. No such proof exists in this codebase. |
| "Exact K41 measurement" | K41 scaling requires validated turbulence data at controlled Reynolds numbers; this module uses symbolic sigma ratios only. |
| "The sigma register predicts NS blow-up" | The register is a fixed audio-synthesis parameter set, not a PDE solution. |
| "Hölder exponent alpha computed here is the true Hölder exponent of any fluid" | `holder_alpha_from_sigma` is a deterministic bijection on a symbolic register, not a field estimator. |

---

## Module Outputs Summary

```
depth=0  sigma=0.0020  alpha=1.0000  (fully regular — depth 0 anchor)
depth=1  sigma=0.0015  alpha≈0.4150  (depth-1 crackle band)
depth=2  sigma=0.0010  alpha=0.5000  (depth-2 micro-pop band)
```

At `omega_norm = 1.0`, `theta_jump = 0`, baseline `alpha_0 = 0.75`:
```
alpha_eff = 0.75 - 0.5 * 1.0 - 0.0 = 0.25
sigma_eff(d=1) = 0.002 * 2^(-0.25) ≈ 0.001682
```

At `omega_norm = 0.9`, `theta_jump = pi`, baseline `alpha_0 = 0.75`:
```
alpha_eff = 0.75 - 0.5*0.9 - 0.25*1.0 = 0.75 - 0.45 - 0.25 = 0.05
sigma_eff(d=2) = 0.002 * 2^(-0.05*2) ≈ 0.001931
```

---

## Next Validation Steps

1. **Synthetic Burgers benchmark** — Generate 1-D Burgers with known blow-up time;
   measure pointwise Hölder exponents via wavelet modulus maxima; compare to `effective_alpha`.
2. **K41 calibration** — Map `sigma_from_holder(0.002, 1/3, d)` for `d ∈ {1,2,3}` and
   compare ratio sequence to measured second-order structure function scaling in a
   pseudospectral NS simulation.
3. **Phase coherence experiment** — Compute Gabor phase across a simulated vortex sheet;
   fit `eta_phase` parameter from measured theta distributions.
4. **Audio texture test** — A/B compare cascade audio at `alpha_eff > 0.3` vs. `< 0.1`;
   document perceptual discriminability as a qualitative falsification record.

---

*This document is part of the MCORE-1 badabing research packet series.*
*No claim made here constitutes a mathematical proof or experimental result.*
