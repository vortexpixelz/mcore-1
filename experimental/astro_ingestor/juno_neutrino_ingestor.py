"""
juno_neutrino_ingestor.py
=========================
MCORE-1 ingestor for JUNO detector supernova neutrino burst data.

Maps PMT hit-rate time series to the ternary trit grammar {-1, 0, +1}
and renders via depth-aware Gabor sonification.

Physical background
-------------------
JUNO (Jiangmen Underground Neutrino Observatory) detects anti-neutrinos
via Inverse Beta Decay (IBD) in 20 kton liquid scintillator.  Background
event rate follows a Poisson distribution.  A core-collapse supernova at
~10 kpc produces a sharp neutrino burst lasting ~10 s, with peak rate
10-25x the background level (Mirizzi et al. 2016).

Trit quantization rule
-----------------------
  lambda_bg = mean background rate
  +1  if rate >  3 * lambda_bg   (primary neutrino wave)
  -1  if rate <  0.5 * lambda_bg (dead-time / instrumental veto)
   0  otherwise                  (Poisson background hum)

Sonification character
-----------------------
The quiet Poisson background produces a steady 60 Hz tension hum.
SN onset fires dense +1 bursts: sharp Gabor clicks cascading at
880/1320/1980 Hz.  Dead-time drops produce brief -1 silence pockets.

CLAIM STATUS
------------
[ESTABLISHED]  np.concatenate Gabor render, integer sample indexing
[ESTABLISHED]  weights_for_check_tree shift: {-1,0,+1} -> {0,1,2}
[PLAUSIBLE]    3x threshold cleanly separates SN signal from Poisson
               fluctuations for the mock data generator used here
[PLAUSIBLE]    Dead-time -1 states map to algebraic gap nodes in the
               conservation tree (qualitative analogy)
[CONJECTURAL]  Trit conservation violations at burst onset correspond
               to physically meaningful stellar core-collapse dynamics
"""

from __future__ import annotations

import argparse
import math
import os
import random

import numpy as np
from scipy.io.wavfile import write

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SAMPLE_RATE   = 48_000
TRIT_DURATION = 0.050   # 50 ms per bin
OUTPUT_DIR    = "mcore_astro_production"

SONI_PARAMS: dict[str, dict] = {
    "hum":       {"freq":   60.0, "sigma": 1.000, "amp": 0.05, "phase": 0.0},
    "primary":   {"freq":  880.0, "sigma": 0.002, "amp": 0.40, "phase":  math.pi / 2},
    "secondary": {"freq": 1320.0, "sigma": 0.0015,"amp": 0.25, "phase": -math.pi / 2},
    "tertiary":  {"freq": 1980.0, "sigma": 0.001, "amp": 0.10, "phase":  math.pi / 2},
}


# ---------------------------------------------------------------------------
# Quantization
# ---------------------------------------------------------------------------

def quantize(hit_rates: list[float], bg_mean: float) -> list[int]:
    """
    Map JUNO hit-rate time series to trit sequence.
    [ESTABLISHED] Deterministic, memoryless finite-state transducer.
    """
    trits: list[int] = []
    for rate in hit_rates:
        if rate > 3.0 * bg_mean:
            trits.append(1)    # Primary neutrino wave
        elif rate < 0.5 * bg_mean:
            trits.append(-1)   # Dead-time / veto
        else:
            trits.append(0)    # Poisson background
    return trits


def weights_for_check_tree(trits: list[int]) -> list[int]:
    """[ESTABLISHED] Shift signed trits to unsigned check_tree weights."""
    return [t + 1 for t in trits]


# ---------------------------------------------------------------------------
# Synthetic data generator
# ---------------------------------------------------------------------------

def generate_mock_juno_data(
    n_bins: int = 100,
    bg_mean: float = 15.0,
    sn_start: int = 40,
) -> tuple[list[float], float]:
    """
    Simulate JUNO PMT hit rates with a core-collapse supernova injection.

    Background: Poisson(lambda=bg_mean)
    Supernova burst at sn_start: peak ~25x background, fast rise + decay
    Dead-time veto injected immediately after the burst peak.

    [PLAUSIBLE] Peak multipliers based on Mirizzi et al. 2016 table for
                a 10 kpc core-collapse event; not a fit to real JUNO data.
    """
    data = [random.gauss(bg_mean, math.sqrt(bg_mean)) for _ in range(n_bins)]

    # Supernova burst: 5-bin profile (fast rise, decay)
    sn_profile = [bg_mean * m for m in [10, 25, 15, 5, 3]]
    for j, val in enumerate(sn_profile):
        if sn_start + j < n_bins:
            data[sn_start + j] = val

    # Instrumental dead-time immediately after burst
    for j in range(2):
        if sn_start + len(sn_profile) + j < n_bins:
            data[sn_start + len(sn_profile) + j] = 2.0 - j

    return data, bg_mean


# ---------------------------------------------------------------------------
# Gabor atom + render  (identical pattern to gjb2_sonification.py)
# ---------------------------------------------------------------------------

def _cascade_state(trit: int, index: int) -> str:
    if trit == 0:
        return "hum"
    return ["primary", "secondary", "tertiary"][index % 3]


def gabor_atom(state: str) -> np.ndarray:
    """[ESTABLISHED] Self-contained Gabor grain, np.concatenate safe."""
    p = SONI_PARAMS[state]
    n = int(SAMPLE_RATE * TRIT_DURATION)
    t = np.linspace(0, TRIT_DURATION, n, endpoint=False)
    mu = TRIT_DURATION / 2
    envelope = np.exp(-0.5 * ((t - mu) / p["sigma"]) ** 2)
    carrier  = np.sin(2 * math.pi * p["freq"] * t + p["phase"])
    return (envelope * carrier * p["amp"]).astype(np.float32)


def render(trits: list[int], filename: str) -> None:
    """[ESTABLISHED] np.concatenate render, -0.5 dBFS peak limiter."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    states = [_cascade_state(t, i) for i, t in enumerate(trits)]
    audio  = np.concatenate([gabor_atom(s) for s in states])

    peak = float(np.max(np.abs(audio)))
    if peak > 0.944:
        audio *= 0.944 / peak

    path = os.path.join(OUTPUT_DIR, filename)
    write(path, SAMPLE_RATE, (audio * 32_767).astype(np.int16))

    dist = {k: trits.count(k) for k in (-1, 0, 1)}
    sz   = os.path.getsize(path) // 1024
    print(f"  [{filename:40s}]  {len(trits):>4} trits | {sz} KB")
    print(f"  Distribution: +1={dist[1]} (burst)  0={dist[0]} (background)  -1={dist[-1]} (veto)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="MCORE-1 JUNO Neutrino Ingestor")
    parser.add_argument("--n-bins",   type=int,   default=100,  help="Number of time bins")
    parser.add_argument("--bg-mean",  type=float, default=15.0, help="Background mean event rate")
    parser.add_argument("--sn-start", type=int,   default=40,   help="Bin index for SN burst injection")
    parser.add_argument("--dry-run",  action="store_true",       help="Print trits only; skip audio")
    args = parser.parse_args()

    print("=" * 60)
    print("MCORE-1 JUNO Neutrino Burst Ingestor")
    print("=" * 60)

    data, bg_mean = generate_mock_juno_data(
        n_bins=args.n_bins, bg_mean=args.bg_mean, sn_start=args.sn_start
    )
    trits   = quantize(data, bg_mean)
    weights = weights_for_check_tree(trits)

    dist = {k: trits.count(k) for k in (-1, 0, 1)}
    print(f"Quantized {len(trits)} time bins")
    print(f"Distribution: +1={dist[1]} (burst)  0={dist[0]} (background)  -1={dist[-1]} (veto)")
    print(f"Weights (0/1/2): {weights}")

    if args.dry_run:
        print("[dry-run] Audio render skipped.")
        return

    render(trits, "juno_neutrino_burst.wav")
    print("\nDone. Feed weights into check_tree for conservation audit.")


if __name__ == "__main__":
    main()
