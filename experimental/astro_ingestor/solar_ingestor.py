"""
solar_ingestor.py
=================
MCORE-1 Astrophysical Ingestion Pipeline — Solar Magnetogram Module
Production Grade v1.1  |  Symonic / ArchēLab  |  May 2026

CLAIM STATUS
------------
[ESTABLISHED]  np.concatenate render pattern matches gjb2_sonification.py;
               integer sample indexing; no float-offset array-boundary bugs.
[ESTABLISHED]  Universal Quantization Function Q(B) is deterministic and
               memoryless — output depends only on current flux value + threshold.
[PLAUSIBLE]    Fractal cascade depth heuristics (L0 run-length thresholds) capture
               qualitative hierarchical tearing motif; not validated vs MHD/PIC.
[CONJECTURAL]  Acoustic output is a physically faithful rendering of solar
               reconnection — quantitative validation is future work.

Architecture
------------
Three strictly decoupled stages (mirrors gjb2_sonification.py):
  1. fetch_solar_slice()      — FITS read or synthetic PIL fallback
  2. quantize_to_trits()      — Universal Quantization Q(B)
  3. process_fractal_cascade() — run-length depth heuristics → event list
  4. render_audio()           — np.concatenate gabor_atom list → WAV

Conservation bridge
-------------------
Pass signed trits to weights_for_check_tree() before calling check_tree:

    from mcore_1.check_tree import check_tree
    weights = weights_for_check_tree(trits)   # {-1,0,+1} → {0,1,2}
    results = check_tree(weights)

Fixed vs draft version
-----------------------
- coalesce event now fires on the first non-zero cell AFTER a zero-run ends
  (draft incorrectly fired on the non-zero cell before appending 'hum').
- Peak limiter uses 0.944 ceiling (-0.5 dBFS) matching astro_mcore_ingestor.py.
- TRIT_DURATION kept at 0.050 s (50 ms) for solar cascade; adjust as needed.
"""

from __future__ import annotations

import os

import numpy as np
from scipy.io.wavfile import write as wav_write

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SAMPLE_RATE: int = 48000
TRIT_DURATION: float = 0.050      # 50 ms per trit
OUTPUT_DIR: str = "mcore_solar_production"

# Depth-aware Gabor parameters — the fractal register
# Matches AstroSonifier in astro_mcore_ingestor.py for cross-pipeline consistency
SONI_PARAMS: dict[str, dict] = {
    "hum":       {"freq": 60.0,   "sigma": 1.0,    "amp": 0.05, "phase": 0.0},
    "primary":   {"freq": 880.0,  "sigma": 0.002,  "amp": 0.40, "phase": np.pi / 2},
    "secondary": {"freq": 1320.0, "sigma": 0.0015, "amp": 0.25, "phase": -np.pi / 2},
    "tertiary":  {"freq": 1980.0, "sigma": 0.001,  "amp": 0.10, "phase": np.pi / 2},
    "coalesce":  {"freq": 440.0,  "sigma": 0.050,  "amp": 0.45, "phase": 0.0},
}


# ---------------------------------------------------------------------------
# Stage 1: Data ingestion
# ---------------------------------------------------------------------------

def fetch_solar_slice(fits_path: str | None = None) -> np.ndarray:
    """Load a 1D PIL-perpendicular slice from an SDO/HMI FITS file.

    Falls back to a synthetic high-shear active-region slice if the file is
    absent, unreadable, or astropy is not installed.
    """
    if fits_path and os.path.exists(fits_path):
        try:
            from astropy.io import fits  # type: ignore
            print(f"Loading live FITS data from {fits_path} ...", end=" ", flush=True)
            with fits.open(fits_path) as hdul:
                data = hdul[1].data if len(hdul) > 1 else hdul[0].data
                row = data.shape[0] // 2
                slice_1d = data[row, 100:200].astype(np.float32)
            print("done.")
            return slice_1d
        except ImportError:
            print("astropy not installed — using synthetic fallback.")
        except Exception as exc:
            print(f"FITS load failed ({exc}) — using synthetic fallback.")

    print("Generating synthetic Polarity Inversion Line (PIL) slice ...")
    rng = np.random.default_rng(42)  # deterministic seed for reproducibility
    return np.concatenate([
        rng.normal(120, 20, 15).astype(np.float32),   # strong +polarity
        rng.normal(0, 25, 30).astype(np.float32),     # neutral sheet / PIL
        rng.normal(-110, 20, 15).astype(np.float32),  # strong -polarity
    ])


# ---------------------------------------------------------------------------
# Stage 2: Universal Quantization  Q(B)
# ---------------------------------------------------------------------------

def quantize_to_trits(
    flux_1d: np.ndarray,
    noise_floor: float = 50.0,
) -> list[int]:
    """Map 1D magnetic flux array to signed trit sequence.

    [ESTABLISHED] Pure deterministic threshold function; no hidden state.

    Parameters
    ----------
    flux_1d    : array of line-of-sight B-field values (Gauss)
    noise_floor: symmetric threshold ε above which flux is considered
                 structurally significant (filters quiet-sun micro-fluctuations)

    Returns
    -------
    list of int in {-1, 0, +1}
    """
    trits: list[int] = []
    for b in flux_1d:
        if b > noise_floor:
            trits.append(1)
        elif b < -noise_floor:
            trits.append(-1)
        else:
            trits.append(0)
    return trits


def weights_for_check_tree(signed_trits: list[int]) -> list[int]:
    """Shift {-1, 0, +1} → {0, 1, 2} for mcore_py check_tree.

    The mora-pooling invariant requires unsigned T = {S1, S2, S3} ≡ {0, 1, 2}.
    """
    return [t + 1 for t in signed_trits]


# ---------------------------------------------------------------------------
# Stage 3: Fractal cascade  →  event list
# ---------------------------------------------------------------------------

def process_fractal_cascade(trits: list[int]) -> list[str]:
    """Map trit sequence to fractal tearing event types.

    [PLAUSIBLE] Run-length thresholds are heuristic proxies for stability
    index Δ' and hierarchical depth d.  Not validated against MHD/PIC.

    Event mapping
    -------------
    trit ≠ 0, preceded by zero-run ≥ 1  → 'coalesce'  (current-sheet resolution)
    trit ≠ 0, no preceding zero-run      → 'hum'       (macro-polarity region)
    trit == 0, run-length == 5           → 'primary'   (primary tearing threshold)
    trit == 0, run-length in {8, 11}     → 'secondary' (γ-boosted crackle)
    trit == 0, run-length > 13, even     → 'tertiary'  (micro-island pops)
    else                                 → 'hum'       (tension build-up)
    """
    events: list[str] = []
    zero_run: int = 0
    prev_was_zero: bool = False

    for trit in trits:
        if trit != 0:
            # FIX: coalescence fires HERE — first non-zero after a zero-run
            if prev_was_zero and zero_run >= 1:
                events.append("coalesce")
            else:
                events.append("hum")
            zero_run = 0
            prev_was_zero = False
        else:
            zero_run += 1
            prev_was_zero = True
            if zero_run < 5:
                events.append("hum")
            elif zero_run == 5:
                events.append("primary")
            elif zero_run in (8, 11):
                events.append("secondary")
            elif zero_run > 13 and zero_run % 2 == 0:
                events.append("tertiary")
            else:
                events.append("hum")

    return events


# ---------------------------------------------------------------------------
# Stage 4: Audio synthesis
# ---------------------------------------------------------------------------

def gabor_atom(state_type: str) -> np.ndarray:
    """Single Gabor atom: A * exp(-(t-μ)²/2σ²) * sin(2πft + φ).

    Integer n = int(SAMPLE_RATE * TRIT_DURATION) guarantees exact block size.
    Concatenating N blocks produces exactly N*n samples — no boundary bleed.
    """
    p = SONI_PARAMS[state_type]
    n = int(SAMPLE_RATE * TRIT_DURATION)
    t = np.linspace(0.0, TRIT_DURATION, n, endpoint=False)
    centre = TRIT_DURATION / 2.0
    gaussian = np.exp(-0.5 * ((t - centre) / p["sigma"]) ** 2)
    sinusoid = np.sin(2.0 * np.pi * p["freq"] * t + p["phase"])
    return (gaussian * sinusoid * p["amp"]).astype(np.float32)


def render_audio(events: list[str], filename: str, output_dir: str = OUTPUT_DIR) -> str:
    """Concatenate Gabor atoms and write 48 kHz 16-bit PCM WAV.

    Matches gjb2_sonification.py production pattern exactly:
      audio = np.concatenate([gabor_atom(e) for e in events])
    """
    os.makedirs(output_dir, exist_ok=True)
    atoms = [gabor_atom(e) for e in events]
    audio: np.ndarray = np.concatenate(atoms) if atoms else np.zeros(SAMPLE_RATE, dtype=np.float32)

    # -0.5 dBFS peak ceiling (matching astro_mcore_ingestor.py: 0.944)
    peak = float(np.max(np.abs(audio)))
    if peak > 0.944:
        audio = audio * (0.944 / peak)

    path = os.path.join(output_dir, filename)
    wav_write(path, SAMPLE_RATE, (audio * 32767).astype(np.int16))

    dist = {k: events.count(k) for k in set(events)}
    size_kb = os.path.getsize(path) // 1024
    print(f"  [{filename:<32s}] {len(events)} events | {dist} | {size_kb} KB")
    return path


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    fits_path: str | None = sys.argv[1] if len(sys.argv) > 1 else None

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("=" * 65)
    print("MCORE-1 Solar Fractal Cascade Ingestor — Production v1.1")
    print("=" * 65)

    # 1. Ingest
    solar_flux = fetch_solar_slice(fits_path)

    # 2. Quantize
    trits = quantize_to_trits(solar_flux, noise_floor=50.0)
    print(f"\nQuantized {len(trits)} cells:  "
          f"+1={trits.count(1)}  0={trits.count(0)}  -1={trits.count(-1)}")

    # 3. Cascade
    print("\nRunning fractal cascade ...")
    events = process_fractal_cascade(trits)

    # 4. Render
    print("\nRendering Gabor sonification ...")
    render_audio(events, "solar_production_cascade.wav")

    # 5. Conservation audit (requires mcore-1 package installed)
    print("\nConservation audit (requires mcore_1 installed):")
    print("  weights = weights_for_check_tree(trits)")
    print("  from mcore_1.check_tree import check_tree")
    print("  results = check_tree(weights)")
    print("  # Look for CONSERVATION / OVERFLOW errors at PIL boundary nodes")

    print(f"\n✅ Done — {OUTPUT_DIR}/solar_production_cascade.wav")
