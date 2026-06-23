"""
ns001_gabor_holder.py
=====================
NS-001 | Gabor-Hölder Toy Diagnostic Module
Symonic / ArchēLab | Experimental — 2026

STATUS: TOY DIAGNOSTIC — NOT PROOF-BEARING
==========================================
This module is a deterministic toy diagnostic that maps the MCORE-1
depth-aware Gabor sigma register to an effective Hölder regularity
exponent.  It is an analogy tool and falsification target only.

CLAIM TIERS
-----------
[ESTABLISHED]  holder_alpha_from_sigma / sigma_from_holder form a
               deterministic bijection for depth > 0 and sigma_d < sigma_0.
               No PDE claim of any kind.
[ESTABLISHED]  effective_alpha is pure arithmetic; no fluid-dynamics claim.
[PLAUSIBLE]    The sigma ratio sigma_2/sigma_0 = 0.5 numerically neighbours
               the K41 Hölder exponent range (1/3, 1); could serve as a
               calibration target against synthetic turbulence benchmarks.
[ANALOGY]      The three-level sigma cascade 0.002 → 0.0015 → 0.001 mirrors
               a Richardson energy cascade structurally.  Depths do not map
               to physical inertial-range scales without external calibration.
[CONJECTURE]   Vorticity-adjusted effective alpha compressing toward zero may
               signal approach to a singularity regime in synthetic fields;
               unvalidated against any real turbulence dataset.
[FORBIDDEN PUBLIC CLAIM]
               MCORE-1 solves Navier-Stokes.  Proof of global regularity.
               Exact K41 measurement before experimental validation.

Register anchors (matched to existing production files)
-------------------------------------------------------
  solar_ingestor.py     SONI_PARAMS["primary"]["sigma"]   = 0.002   (depth 0)
  solar_ingestor.py     SONI_PARAMS["secondary"]["sigma"] = 0.0015  (depth 1)
  solar_ingestor.py     SONI_PARAMS["tertiary"]["sigma"]  = 0.001   (depth 2)
  astro_mcore_ingestor  _DEPTH_PARAMS[0]["sigma"]          = 0.002
  astro_mcore_ingestor  _DEPTH_PARAMS[1]["sigma"]          = 0.0015
  astro_mcore_ingestor  _DEPTH_PARAMS[2]["sigma"]          = 0.001
  audio.py              SIGMA_GAUSS                        = 0.008   (GJB2 atom)

See also: docs/badabing/NS001_GABOR_HOLDER_VORTICITY_PACKET.md
"""

from __future__ import annotations

import math

__all__ = [
    "holder_alpha_from_sigma",
    "sigma_from_holder",
    "effective_alpha",
    "sigma_band",
    "vorticity_phase_table",
    "SIGMA_REGISTER",
    "ALPHA_BAND",
]

# ---------------------------------------------------------------------------
# Register anchors — matches solar_ingestor.py and astro_mcore_ingestor.py
# ---------------------------------------------------------------------------

SIGMA_REGISTER: dict[int, float] = {
    0: 0.002,    # depth 0 — primary nucleation / tearing
    1: 0.0015,   # depth 1 — secondary crackle
    2: 0.001,    # depth 2 — tertiary micro-pop
}


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def holder_alpha_from_sigma(sigma_d: float, sigma_0: float, depth: int) -> float:
    """Map a depth-d Gabor sigma to a Hölder regularity exponent alpha.

    [ESTABLISHED] Deterministic bijection for depth > 0 and sigma_d < sigma_0;
    no PDE claim.

    Cascade model:  sigma_d = sigma_0 * 2^(-alpha * depth)
    Solving:        alpha   = log2(sigma_0 / sigma_d) / depth

    Returns alpha = 1.0 for depth <= 0 or sigma_d >= sigma_0 (fully regular).
    Result is clamped to [0, 1].

    Parameters
    ----------
    sigma_d : Gabor sigma at depth d (seconds)
    sigma_0 : Reference sigma at depth 0 (seconds)
    depth   : Cascade depth (non-negative integer)

    Returns
    -------
    alpha in [0, 1]  (0 = maximally rough, 1 = Lipschitz smooth)
    """
    if depth <= 0 or sigma_d >= sigma_0:
        return 1.0
    alpha = math.log2(sigma_0 / sigma_d) / depth
    return max(0.0, min(1.0, alpha))


def sigma_from_holder(sigma_0: float, alpha: float, depth: int) -> float:
    """Recover the depth-d Gabor sigma from a Hölder exponent alpha.

    [ESTABLISHED] Deterministic inverse of holder_alpha_from_sigma
    (for depth > 0 and sigma_d < sigma_0).

    Cascade model: sigma_d = sigma_0 * 2^(-alpha * depth)

    sigma is monotonically decreasing in alpha (for fixed depth > 0):
    higher alpha (smoother) → sigma compresses toward 0;
    lower alpha (rougher)   → sigma expands toward sigma_0.
    sigma also compresses toward 0 as depth increases for any alpha > 0.

    Parameters
    ----------
    sigma_0 : Reference sigma at depth 0 (seconds)
    alpha   : Hölder regularity exponent in [0, 1]
    depth   : Cascade depth (non-negative integer)

    Returns
    -------
    sigma_d (seconds)
    """
    return sigma_0 * (2.0 ** (-alpha * depth))


def effective_alpha(
    alpha_0: float,
    omega_norm: float,
    theta_jump: float = 0.0,
    lambda_omega: float = 0.5,
    eta_phase: float = 0.25,
) -> float:
    """Compute vorticity/phase-adjusted effective Hölder exponent.

    [CONJECTURE] A toy proxy for regularity loss under rising vorticity
    and phase discontinuity.  Not validated against any NS solution.

    Additive reduction model:
        alpha_eff = alpha_0
                  - lambda_omega * omega_norm
                  - eta_phase   * |theta_jump| / pi

    Result is clamped to [0, 1].

    Parameters
    ----------
    alpha_0     : Baseline Hölder exponent (from holder_alpha_from_sigma)
    omega_norm  : Normalised vorticity magnitude ||omega|| / ||omega||_ref >= 0
    theta_jump  : Gabor phase discontinuity at depth boundary (radians)
    lambda_omega: Vorticity coupling weight (default 0.5)
    eta_phase   : Phase-jump coupling weight (default 0.25)

    Returns
    -------
    alpha_eff in [0, 1]
    """
    reduction = lambda_omega * omega_norm + eta_phase * abs(theta_jump) / math.pi
    return max(0.0, min(1.0, alpha_0 - reduction))


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

def sigma_band(
    sigma_0: float = 0.002,
    sigma_1: float = 0.0015,
    sigma_2: float = 0.001,
) -> list[dict]:
    """Return the alpha band for the canonical three-level sigma register.

    [ESTABLISHED] Pure deterministic computation over the register anchors.

    Returns a list of dicts with keys: depth, sigma, alpha.
    """
    anchors = [(0, sigma_0), (1, sigma_1), (2, sigma_2)]
    return [
        {
            "depth": d,
            "sigma": s,
            "alpha": holder_alpha_from_sigma(s, sigma_0, d),
        }
        for d, s in anchors
    ]


# Pre-compute the canonical alpha band at import time (module constant).
ALPHA_BAND: list[dict] = sigma_band()


def vorticity_phase_table(
    alpha_0: float,
    omega_norms: list[float],
    theta_jumps: list[float] | None = None,
    depth: int = 1,
    sigma_0: float = 0.002,
) -> list[dict]:
    """Sweep omega/theta values and return effective alpha and sigma_eff per step.

    [CONJECTURE] sigma_eff from the holder model is an analogy target; not
    validated against real turbulence datasets or NS solutions.

    Note on direction: rising omega_norm reduces alpha_eff, which *increases*
    sigma_eff (sigma = sigma_0 * 2^(-alpha*depth) is decreasing in alpha).

    Parameters
    ----------
    alpha_0     : Baseline Hölder exponent
    omega_norms : Normalised vorticity values to sweep
    theta_jumps : Phase jumps (radians); defaults to [0.0] * len(omega_norms).
                  Must have the same length as omega_norms if provided.
    depth       : Cascade depth for sigma_eff
    sigma_0     : Reference sigma (seconds)

    Returns
    -------
    List of dicts: omega_norm, theta_jump, alpha_eff, sigma_eff
    """
    if theta_jumps is not None and len(theta_jumps) != len(omega_norms):
        raise ValueError(
            f"theta_jumps length ({len(theta_jumps)}) must match "
            f"omega_norms length ({len(omega_norms)})"
        )
    if theta_jumps is None:
        theta_jumps = [0.0] * len(omega_norms)
    rows = []
    for omega, theta in zip(omega_norms, theta_jumps):
        a_eff = effective_alpha(alpha_0, omega, theta)
        rows.append({
            "omega_norm": omega,
            "theta_jump": theta,
            "alpha_eff": a_eff,
            "sigma_eff": sigma_from_holder(sigma_0, a_eff, depth),
        })
    return rows


# ---------------------------------------------------------------------------
# CLI demonstration
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 65)
    print("NS-001 Gabor-Hölder Toy Diagnostic  [EXPERIMENTAL]")
    print("NOT PROOF-BEARING — see module docstring for claim tiers")
    print("=" * 65)

    # 1. Sigma register → alpha band
    print("\n--- Sigma register → Hölder alpha band ---")
    band = sigma_band(sigma_0=0.002, sigma_1=0.0015, sigma_2=0.001)
    for row in band:
        d, s, a = row["depth"], row["sigma"], row["alpha"]
        bar = "#" * int(a * 30)
        print(f"  depth={d}  sigma={s:.4f}  alpha={a:.4f}  [{bar:<30s}]")

    # 2. Round-trip sanity check
    print("\n--- Round-trip sigma <-> alpha (sanity check) ---")
    for row in band[1:]:  # depth=0 is trivially 1.0
        d, s = row["depth"], row["sigma"]
        a = holder_alpha_from_sigma(s, 0.002, d)
        s_back = sigma_from_holder(0.002, a, d)
        ok = "OK" if abs(s_back - s) < 1e-12 else "FAIL"
        print(f"  depth={d}  alpha={a:.6f}  sigma_back={s_back:.6f}  [{ok}]")

    # 3. Rising omega_norm, zero phase jump.
    # alpha_0=0.75 is an above-register value chosen to show the full
    # vorticity reduction range (actual depth-1 register alpha is ~0.415).
    print("\n--- Rising vorticity -> alpha_eff reduction (theta=0) ---")
    omegas = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.5]
    table = vorticity_phase_table(
        alpha_0=0.75,
        omega_norms=omegas,
        depth=1,
        sigma_0=0.002,
    )
    print(f"  {'omega_norm':>10}  {'alpha_eff':>10}  {'sigma_eff(d=1)':>14}")
    for row in table:
        print(
            f"  {row['omega_norm']:>10.2f}"
            f"  {row['alpha_eff']:>10.4f}"
            f"  {row['sigma_eff']:>14.6f}"
        )

    # 4. Rising vorticity + phase jump together
    print("\n--- Rising vorticity + phase jump -> compounded alpha reduction ---")
    omegas2 = [0.0, 0.3, 0.6, 0.9]
    jumps2  = [0.0, math.pi / 4, math.pi / 2, math.pi]
    table2 = vorticity_phase_table(
        alpha_0=0.75,
        omega_norms=omegas2,
        theta_jumps=jumps2,
        depth=2,
        sigma_0=0.002,
    )
    print(
        f"  {'omega_norm':>10}  {'theta_jump/pi':>13}"
        f"  {'alpha_eff':>10}  {'sigma_eff(d=2)':>14}"
    )
    for row in table2:
        theta_pi = row["theta_jump"] / math.pi
        print(
            f"  {row['omega_norm']:>10.2f}"
            f"  {theta_pi:>13.3f}"
            f"  {row['alpha_eff']:>10.4f}"
            f"  {row['sigma_eff']:>14.6f}"
        )

    print("\n[ANALOGY] At fixed alpha, sigma compresses with depth (Richardson cascade analogy).")
    print("[CONJECTURE] alpha_eff -> 0 is a falsification target for NS blow-up proxies.")
    print("[FORBIDDEN] No global regularity claim. No NS proof. No exact K41.")
    print("=" * 65)
