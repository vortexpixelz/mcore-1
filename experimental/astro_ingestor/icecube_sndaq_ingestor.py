"""
icecube_sndaq_ingestor.py
=========================
MCORE-1 ingestor for IceCube SNDAQ (Supernova Data Acquisition) telemetry.

Maps IceCube global DOM hit-rate time series to the ternary trit
grammar {-1, 0, +1} using a z-score deviation metric, then renders
via depth-aware Gabor sonification with a cold 45 Hz tension hum.

Physical background
-------------------
IceCube does not detect individual SN neutrino events (too low energy
for individual vertex reconstruction).  Instead, SNDAQ monitors the
collective hit rate across all ~5160 Digital Optical Modules (DOMs)
for a correlated global rate increase.  The dominant background is
atmospheric muons (~2800 Hz/DOM).  A core-collapse SN at 10 kpc
produces a ~0.3% collective rate increase above this dense baseline
(Abbasi et al. 2011, A&A 535 A109).

Why z-score instead of flat threshold
--------------------------------------
Unlike JUNO (clean PMT, Poisson noise), IceCube's muon background
fluctuates significantly.  A flat rate threshold would fire constantly.
The correct discriminant is the normalized deviation from a sliding
background window:

    z = (rate - mu_bg) / sigma_bg

Trit quantization rule
-----------------------
  z = (rate - bg_mean) / bg_std
  +1  if z >  5.0   (5-sigma collective SN wavefront)
  -1  if z < -3.0   (DAQ dead-time / veto)
   0  otherwise     (atmospheric muon background hum)

Sonification character
-----------------------
The cold, dense muon background maps to a 45 Hz tension hum (colder
than the standard 60 Hz to reflect IceCube's 1.5 km deep Antarctic
Ice environment).  The rare +1 states cascade in sharp Gabor clicks
at 880/1320/1980 Hz, audibly distinct from the sub-bass baseline.

CLAIM STATUS
------------
[ESTABLISHED]  np.concatenate Gabor render, integer sample indexing
[ESTABLISHED]  weights_for_check_tree shift: {-1,0,+1} -> {0,1,2}
[ESTABLISHED]  5-sigma threshold consistent with SNDAQ alert criteria
               (IceCube uses 5-sigma for public SN alerts)
[PLAUSIBLE]    Cold 45 Hz hum captures qualitative density of muon
               background vs. JUNO's cleaner Poisson regime
[PLAUSIBLE]    z-score quantization correctly isolates collective rate
               increase from per-DOM fluctuations
[CONJECTURAL]  Trit carry-cascade topology of the SN wavefront encodes
               universal cross-domain structural information comparable
               to the GJB2 frameshift carry cascade
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
TRIT_DURATION = 0.050   # 50 ms per 2 ms IceCube SNDAQ bin (oversampled for audio)
OUTPUT_DIR    = "mcore_astro_production"

# Cold IceCube register: 45 Hz instead of standard 60 Hz
# [PLAUSIBLE] Qualitative choice reflecting Antarctic ice medium
SONI_PARAMS: dict[str, dict] = {
    "hum":       {"freq":   45.0, "sigma": 1.000, "amp": 0.03, "phase": 0.0},
    "primary":   {"freq":  880.0, "sigma": 0.002, "amp": 0.40, "phase":  math.pi / 2},
    "secondary": {"freq": 1320.0, "sigma": 0.0015,"amp": 0.25, "phase": -math.pi / 2},
    "tertiary":  {"freq": 1980.0, "sigma": 0.001, "amp": 0.10, "phase":  math.pi / 2},
}

SN_SIGMA_THRESHOLD   =  5.0   # [ESTABLISHED] IceCube SNDAQ public alert threshold
VETO_SIGMA_THRESHOLD = -3.0   # DAQ dead-time floor


# ---------------------------------------------------------------------------
# Quantization
# ---------------------------------------------------------------------------

def quantize(
    hit_rates: list[float],
    bg_mean: float,
    bg_std: float,
    sn_threshold: float = SN_SIGMA_THRESHOLD,
    veto_threshold: float = VETO_SIGMA_THRESHOLD,
) -> list[int]:
    """
    Map IceCube global hit-rate bins to trit sequence via z-score.
    [ESTABLISHED] Deterministic, memoryless finite-state transducer.
    [ESTABLISHED] 5-sigma threshold matches IceCube SNDAQ alert criteria.
    """
    trits: list[int] = []
    for rate in hit_rates:
        z = (rate - bg_mean) / bg_std
        if z > sn_threshold:
            trits.append(1)    # Supernova wavefront collective spike
        elif z < veto_threshold:
            trits.append(-1)   # DAQ dead-time / veto artifact
        else:
            trits.append(0)    # Atmospheric muon background
    return trits


def weights_for_check_tree(trits: list[int]) -> list[int]:
    """[ESTABLISHED] Shift signed trits to unsigned check_tree weights."""
    return [t + 1 for t in trits]


# ---------------------------------------------------------------------------
# Synthetic data generator
# ---------------------------------------------------------------------------

def generate_mock_icecube_data(
    n_bins: int = 300,
    bg_mean: float = 1.5e6,
    bg_std:  float = 1.2e3,
    sn_start: int = 100,
) -> tuple[list[float], float, float]:
    """
    Simulate 15 seconds of IceCube SNDAQ global hit rates.

    Background: Gaussian(bg_mean, bg_std) approximating the combined
    Poisson + muon fluctuation regime at the full detector scale.
    SN signal: fast-rise exponential decay profile starting at sn_start,
    matching the canonical core-collapse neutrino lightcurve shape.
    Dead-time: brief veto artifact injected after peak burst.

    [PLAUSIBLE] Signal amplitude (1e4 * t^2 * exp(-t/0.5)) is a
                representative toy model; not fit to a real IceCube event.
    [PLAUSIBLE] bg_mean=1.5e6 is a simplified aggregate; real SNDAQ
                uses per-DOM rates and more sophisticated noise models.
    """
    data = [random.gauss(bg_mean, bg_std) for _ in range(n_bins)]

    # Inject core-collapse SN neutrino lightcurve
    for i in range(sn_start, min(sn_start + 40, n_bins)):
        t_sn = (i - sn_start) * 0.05   # seconds since burst onset
        sn_signal = 1.0e4 * (t_sn ** 2) * math.exp(-t_sn / 0.5)
        data[i] += sn_signal

    # Inject instrumental dead-time veto after burst peak
    veto_start = sn_start + 45
    for j in range(3):
        if veto_start + j < n_bins:
            data[veto_start + j] = bg_mean - (4.0 * bg_std)

    return data, bg_mean, bg_std


# ---------------------------------------------------------------------------
# Gabor atom + render
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
    print(f"  Distribution: +1={dist[1]} (SN)  0={dist[0]} (muon bg)  -1={dist[-1]} (veto)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="MCORE-1 IceCube SNDAQ Ingestor")
    parser.add_argument("--n-bins",    type=int,   default=300,    help="Number of time bins (default 300 = 15 s)")
    parser.add_argument("--sn-start",  type=int,   default=100,    help="Bin index for SN burst injection")
    parser.add_argument("--sn-thresh", type=float, default=5.0,    help="Sigma threshold for SN detection")
    parser.add_argument("--dry-run",   action="store_true",         help="Print trits only; skip audio")
    args = parser.parse_args()

    print("=" * 60)
    print("MCORE-1 IceCube SNDAQ Ingestor")
    print("=" * 60)

    data, bg_mean, bg_std = generate_mock_icecube_data(
        n_bins=args.n_bins, sn_start=args.sn_start
    )
    trits   = quantize(data, bg_mean, bg_std, sn_threshold=args.sn_thresh)
    weights = weights_for_check_tree(trits)

    dist = {k: trits.count(k) for k in (-1, 0, 1)}
    print(f"Quantized {len(trits)} SNDAQ bins")
    print(f"Distribution: +1={dist[1]} (SN wavefront)  0={dist[0]} (muon bg)  -1={dist[-1]} (veto)")
    print(f"Weights (0/1/2): {weights}")

    if args.dry_run:
        print("[dry-run] Audio render skipped.")
        return

    render(trits, "icecube_sn_cascade.wav")
    print("\nDone. Feed weights into check_tree for conservation audit.")
    print("Note: Real IceCube SNDAQ data available at https://snews2.org")


if __name__ == "__main__":
    main()
