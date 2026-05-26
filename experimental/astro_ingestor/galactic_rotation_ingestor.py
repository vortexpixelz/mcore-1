"""
galactic_rotation_ingestor.py
==============================
MCORE-1 ingestor for galactic rotation curve data.

Maps observed vs. Keplerian rotational velocity deviation into the
ternary trit grammar {-1, 0, +1} and renders via depth-aware Gabor
sonification.

Physical background
-------------------
In a purely baryonic galaxy the orbital velocity at radius r should
fall as v ~ 1/sqrt(r) (Keplerian).  Observed rotation curves remain
flat far beyond the luminous disk, implying an extended dark matter
halo that adds mass at all radii (Rubin & Ford 1970; SPARC catalogue).

Trit quantization rule
----------------------
  epsilon_v = 15 km/s  (threshold margin)
  delta = v_obs - v_kep
  +1  if delta >  epsilon_v  (excess velocity -> dark matter signature)
  -1  if delta < -epsilon_v  (anomalous drag)
   0  otherwise              (baryonic / consistent with Keplerian)

Sonification character
-----------------------
Flat rotation curves sustain prolonged +1 states, driving the
MCORE-1 cascade to accumulate high local stress.  The result is a
rising crackle cascade punctuated by fractal tearing bursts.

CLAIM STATUS
------------
[ESTABLISHED]  np.concatenate Gabor render, integer sample indexing
[ESTABLISHED]  weights_for_check_tree shift: {-1,0,+1} -> {0,1,2}
[PLAUSIBLE]    Flat-curve +1 saturation maps qualitatively to sustained
               topological stress in the MCORE-1 cascade
[CONJECTURAL]  Trit conservation violations correspond to physically
               meaningful dark matter density discontinuities
"""

from __future__ import annotations

import argparse
import math
import os
import random
from typing import Optional

import numpy as np
from scipy.io.wavfile import write

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SAMPLE_RATE   = 48_000
TRIT_DURATION = 0.100   # 100 ms per trit (rotation curves are slow-varying)
OUTPUT_DIR    = "mcore_astro_production"
VELOCITY_THRESHOLD = 15.0  # km/s  [ESTABLISHED: deterministic rule]

SONI_PARAMS: dict[str, dict] = {
    "hum":       {"freq":   60.0, "sigma": 1.000, "amp": 0.05, "phase": 0.0},
    "primary":   {"freq":  880.0, "sigma": 0.002, "amp": 0.40, "phase":  math.pi / 2},
    "secondary": {"freq": 1320.0, "sigma": 0.0015,"amp": 0.25, "phase": -math.pi / 2},
    "tertiary":  {"freq": 1980.0, "sigma": 0.001, "amp": 0.10, "phase":  math.pi / 2},
}


# ---------------------------------------------------------------------------
# Quantization
# ---------------------------------------------------------------------------

def quantize(v_obs: list[float], v_kep: list[float],
             threshold: float = VELOCITY_THRESHOLD) -> list[int]:
    """
    Map (observed, Keplerian) velocity pairs to trit sequence.
    [ESTABLISHED] Deterministic, memoryless finite-state transducer.
    """
    trits: list[int] = []
    for obs, kep in zip(v_obs, v_kep):
        delta = obs - kep
        if delta > threshold:
            trits.append(1)    # Dark matter excess
        elif delta < -threshold:
            trits.append(-1)   # Anomalous drag
        else:
            trits.append(0)    # Baryonic baseline
    return trits


def weights_for_check_tree(trits: list[int]) -> list[int]:
    """Shift signed trits to unsigned weights for mcore_py check_tree.
    [ESTABLISHED] Matches mcore_py algebra invariant exactly.
    """
    return [t + 1 for t in trits]


# ---------------------------------------------------------------------------
# Synthetic data generator
# ---------------------------------------------------------------------------

def generate_mock_rotation_curve(
    n_radii: int = 60,
    flat_velocity: float = 190.0,
    keplerian_scale: float = 250.0,
    inner_cutoff: int = 8,
    noise_sigma: float = 5.0,
) -> tuple[list[int], list[float], list[float]]:
    """
    Simulate a SPARC-style rotation curve.

    Inner region (<inner_cutoff kpc): Keplerian falloff.
    Outer region (>=inner_cutoff kpc): flat curve indicating dark matter halo.

    [PLAUSIBLE] Parameters are representative of typical late-type spirals
                (e.g., NGC 6503, UGC 2885); not fit to a specific object.
    """
    radii = list(range(1, n_radii + 1))
    v_kep = [keplerian_scale / math.sqrt(r) for r in radii]
    v_obs: list[float] = []
    for r in radii:
        if r < inner_cutoff:
            v_obs.append(keplerian_scale / math.sqrt(r) + random.gauss(0, noise_sigma / 2))
        else:
            v_obs.append(flat_velocity + random.gauss(0, noise_sigma))
    return radii, v_obs, v_kep


# ---------------------------------------------------------------------------
# Gabor atom + render
# ---------------------------------------------------------------------------

def _cascade_state(trit: int, index: int) -> str:
    """Map trit value and index to a named Gabor register."""
    if trit == 0:
        return "hum"
    depth = index % 3
    return ["primary", "secondary", "tertiary"][depth]


def gabor_atom(state: str) -> np.ndarray:
    """Single self-contained Gabor grain.
    [ESTABLISHED] np.concatenate pattern; no float t_offset drift.
    """
    p = SONI_PARAMS[state]
    n = int(SAMPLE_RATE * TRIT_DURATION)
    t = np.linspace(0, TRIT_DURATION, n, endpoint=False)
    mu = TRIT_DURATION / 2
    envelope = np.exp(-0.5 * ((t - mu) / p["sigma"]) ** 2)
    carrier  = np.sin(2 * math.pi * p["freq"] * t + p["phase"])
    return (envelope * carrier * p["amp"]).astype(np.float32)


def render(trits: list[int], filename: str) -> None:
    """Concatenate Gabor atoms and write normalised PCM 16-bit WAV.
    [ESTABLISHED] Matches gjb2_sonification.py render discipline.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    states = [_cascade_state(t, i) for i, t in enumerate(trits)]
    audio  = np.concatenate([gabor_atom(s) for s in states])

    peak = float(np.max(np.abs(audio)))
    if peak > 0.944:
        audio *= 0.944 / peak   # -0.5 dBFS ceiling

    path = os.path.join(OUTPUT_DIR, filename)
    write(path, SAMPLE_RATE, (audio * 32_767).astype(np.int16))

    dist = {k: trits.count(k) for k in (-1, 0, 1)}
    sz   = os.path.getsize(path) // 1024
    print(f"  [{filename:40s}]  {len(trits):>4} trits | {sz} KB")
    print(f"  Distribution: +1={dist[1]}  0={dist[0]}  -1={dist[-1]}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="MCORE-1 Galactic Rotation Ingestor")
    parser.add_argument("--n-radii",   type=int,   default=60,    help="Number of radial bins")
    parser.add_argument("--threshold", type=float, default=15.0,  help="Velocity threshold epsilon_v (km/s)")
    parser.add_argument("--dry-run",   action="store_true",        help="Print trits only; skip audio")
    args = parser.parse_args()

    print("=" * 60)
    print("MCORE-1 Galactic Rotation Curve Ingestor")
    print("=" * 60)

    radii, v_obs, v_kep = generate_mock_rotation_curve(n_radii=args.n_radii)
    trits   = quantize(v_obs, v_kep, threshold=args.threshold)
    weights = weights_for_check_tree(trits)

    dist = {k: trits.count(k) for k in (-1, 0, 1)}
    print(f"Quantized {len(trits)} radial bins")
    print(f"Distribution: +1={dist[1]} (dark matter)  0={dist[0]} (baryonic)  -1={dist[-1]} (drag)")
    print(f"Weights (0/1/2): {weights}")

    if args.dry_run:
        print("[dry-run] Audio render skipped.")
        return

    render(trits, "galactic_rotation_cascade.wav")
    print("\nDone. Feed weights into check_tree for conservation audit.")


if __name__ == "__main__":
    main()
