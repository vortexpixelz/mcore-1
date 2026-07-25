"""
astro_mcore_ingestor.py
=======================
EXPERIMENTAL — astro-mcore-ingestor skill
Symonic / ArchēLab — Origami Axioms Program

CLAIM STATUS
------------
[ESTABLISHED]   Deterministic trit quantization is a pure rule-based function;
                output is fully reproducible given identical input.
[ESTABLISHED]   Gabor render pattern mirrors gjb2_sonification.py production code
                (integer sample indexing, np.concatenate, -0.5 dBFS clip).
[PLAUSIBLE]     Trit sequences from these ingestors, when passed to check_tree,
                will surface CONSERVATION / OVERFLOW errors consistent with the
                mora-pooling invariant — no cross-domain validation yet performed.
[CONJECTURAL]   Acoustic output meaningfully represents dark matter dynamics,
                neutrino burst physics, or pulsar magnetosphere structure.
                Quantitative physical validation is future work.

Conservation bridge
-------------------
The MCORE-1 algebra operates on T = {S1, S2, S3} ≡ {0, 1, 2}.
The signed trit alphabet {-1, 0, +1} used here must be shifted +1
before passing to check_tree:

    weights_for_checker = [t + 1 for t in signed_trits]  # → {0, 1, 2}

This preserves the parent == trit_add_seq(children) invariant.

Sonification pattern
--------------------
Matches gjb2_sonification.py exactly:
  SAMPLE_RATE    = 48000
  TRIT_DURATION  = 0.100   (100 ms; GJB2 uses 40 ms — adjustable)
  GAUSSIAN_SIGMA = 0.008
Each trit renders as a Gabor atom: A * exp(-t²/2σ²) * sin(2πft)
Depth-aware parameters mirror the fractal cascade hierarchy.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import numpy as np
from scipy.io.wavfile import write as wav_write

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SAMPLE_RATE: int = 48000
TRIT_DURATION: float = 0.100      # 100 ms per trit (adjust to taste)
GAUSSIAN_SIGMA: float = 0.008     # 8 ms Gaussian window

# Depth-aware sonification parameters
# depth 0 = primary nucleation / tearing
# depth 1 = secondary crackle
# depth 2 = tertiary micro-pop
# neutral (0-state) = sustained tension hum
_DEPTH_PARAMS: dict[int | str, dict] = {
    0:         {"freq": 880,  "sigma": 0.002,  "amp": 0.40},
    1:         {"freq": 1320, "sigma": 0.0015, "amp": 0.25},
    2:         {"freq": 1980, "sigma": 0.001,  "amp": 0.10},
    "neutral": {"freq": 60,   "sigma": 1.0,    "amp": 0.05},
}


# ---------------------------------------------------------------------------
# Gabor atom (production pattern — matches gjb2_sonification.py)
# ---------------------------------------------------------------------------

def _gabor_atom(
    freq: float,
    sigma: float,
    amp: float,
    duration: float = TRIT_DURATION,
    sample_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    """Single Gabor atom: Gaussian-windowed sinusoid.

    Satisfies σ_t * σ_f ≥ 1/(4π); empirical excess ≈1.12× for σ=0.008 s
    (finite-sample discretisation — see gjb2_sonification analysis).
    """
    n = int(sample_rate * duration)
    t = np.linspace(0.0, duration, n, endpoint=False)
    centre = duration / 2.0
    gaussian = np.exp(-0.5 * ((t - centre) / sigma) ** 2)
    sinusoid = np.sin(2.0 * np.pi * freq * t)
    return (amp * gaussian * sinusoid).astype(np.float32)


# ---------------------------------------------------------------------------
# Base sonifier
# ---------------------------------------------------------------------------

class AstroSonifier:
    """Base class: depth-aware Gabor render for signed trit sequences.

    Signed trit convention: -1 = negative polarity / deficit / interpulse
                             0 = neutral / current sheet / baseline
                            +1 = positive polarity / spike / main pulse

    Render maps non-zero trits to depth-cycled Gabor atoms;
    zero trits render as a sustained low-frequency tension hum.
    """

    def render(
        self,
        signed_trits: list[int],
        filename: str,
        output_dir: str = "astro_sonification",
    ) -> str:
        """Render signed trit sequence to a WAV file.

        Uses integer sample indexing throughout (no float-index bugs).
        Returns the absolute path to the written file.
        """
        os.makedirs(output_dir, exist_ok=True)
        atoms: list[np.ndarray] = []
        depth_cycle = 0
        for trit in signed_trits:
            if trit == 0:
                p = _DEPTH_PARAMS["neutral"]
            else:
                p = _DEPTH_PARAMS[depth_cycle % 3]
                depth_cycle += 1
            atoms.append(_gabor_atom(p["freq"], p["sigma"], p["amp"]))
        audio = np.concatenate(atoms) if atoms else np.zeros(SAMPLE_RATE, dtype=np.float32)
        audio = np.clip(audio, -0.944, 0.944)  # -0.5 dBFS safety ceiling
        path = os.path.join(output_dir, filename)
        wav_write(path, SAMPLE_RATE, (audio * 32767).astype(np.int16))
        return path

    @staticmethod
    def weights_for_check_tree(signed_trits: list[int]) -> list[int]:
        """Shift signed {-1, 0, +1} → unsigned {0, 1, 2} for mcore_py check_tree.

        Usage::

            from mcore_1.check_tree import check_tree
            weights = AstroSonifier.weights_for_check_tree(signed_trits)
            results = check_tree(weights)
        """
        return [t + 1 for t in signed_trits]


# ---------------------------------------------------------------------------
# 1. Galactic Rotation Ingestor
# [PLAUSIBLE] Δv threshold captures qualitative dark matter halo signature.
# [CONJECTURAL] Acoustic crackle texture corresponds to halo substructure.
# ---------------------------------------------------------------------------

@dataclass
class GalacticRotationIngestor(AstroSonifier):
    """Detect dark matter signatures in galactic rotation curves.

    Quantization rule (deterministic threshold transducer)::

        Δv = v_observed(r) − v_Keplerian(r)
        Δv > +threshold  →  +1   (excess velocity — dark matter support)
        Δv < -threshold  →  -1   (deficit — anomalous drag / artifact)
        else             →   0   (consistent with baryonic matter)

    The 15 km/s default is larger than typical measurement uncertainties
    while sensitive to the ~20–50 km/s flat-curve anomalies in the literature.
    """

    velocity_threshold: float = 15.0  # km/s

    def quantize(
        self,
        observed_velocity: np.ndarray,
        keplerian_velocity: np.ndarray,
    ) -> list[int]:
        """Map Δv array to signed trit sequence."""
        delta_v = np.asarray(observed_velocity) - np.asarray(keplerian_velocity)
        trits: list[int] = []
        for dv in delta_v:
            if dv > self.velocity_threshold:
                trits.append(1)
            elif dv < -self.velocity_threshold:
                trits.append(-1)
            else:
                trits.append(0)
        return trits


# ---------------------------------------------------------------------------
# 2. JUNO Neutrino Burst Ingestor
# [PLAUSIBLE] 3σ spike detection captures the qualitative supernova neutrino
#             light-curve structure.
# [CONJECTURAL] Cascade depth mirrors physical neutrino emission phases.
# ---------------------------------------------------------------------------

@dataclass
class JunoNeutrinoIngestor(AstroSonifier):
    """Capture supernova neutrino burst dynamics from PMT hit rates.

    Quantization rule::

        R(t) > spike_factor  × R_bg  →  +1   (significant neutrino flux spike)
        R(t) < veto_factor   × R_bg  →  -1   (dead-time veto / electronics glitch)
        else                         →   0   (baseline background)

    Thresholds are conservative by design: 3σ above / 0.5× below background.
    """

    spike_factor: float = 3.0   # multiples of background for +1
    veto_factor: float = 0.5    # fraction of background for -1

    def quantize(
        self,
        pmt_hit_rate: np.ndarray,
        background_rate: float,
    ) -> list[int]:
        """Map PMT hit-rate array to signed trit sequence."""
        rates = np.asarray(pmt_hit_rate, dtype=float)
        trits: list[int] = []
        for r in rates:
            if r > self.spike_factor * background_rate:
                trits.append(1)
            elif r < self.veto_factor * background_rate:
                trits.append(-1)
            else:
                trits.append(0)
        return trits


# ---------------------------------------------------------------------------
# 3. Pulsar Signal Ingestor
# [PLAUSIBLE] Main/interpulse/off-pulse mapping captures hierarchical beam
#             structure of neutron star radio emission.
# [CONJECTURAL] Periodic trit pattern encodes physically meaningful rotation info.
# ---------------------------------------------------------------------------

@dataclass
class PulsarSignalIngestor(AstroSonifier):
    """Encode periodic neutron star radio beam structure.

    Quantization rule::

        F(t) > main_factor   × F_base  →  +1   (main pulse — primary beam crossing)
        F(t) > inter_factor  × F_base  →  -1   (interpulse — secondary beam crossing)
        else                           →   0   (off-pulse — current-sheet equivalent)

    The asymmetric threshold (+1 stronger than -1) mirrors the observed
    main-pulse / interpulse amplitude ratio in most canonical pulsars.
    """

    main_factor: float = 5.0    # main pulse threshold (× baseline)
    inter_factor: float = 2.0   # interpulse threshold (× baseline)

    def quantize(
        self,
        radio_flux: np.ndarray,
        baseline_flux: float,
    ) -> list[int]:
        """Map radio flux array to signed trit sequence."""
        flux = np.asarray(radio_flux, dtype=float)
        trits: list[int] = []
        for f in flux:
            if f > self.main_factor * baseline_flux:
                trits.append(1)
            elif f > self.inter_factor * baseline_flux:
                trits.append(-1)
            else:
                trits.append(0)
        return trits


# ---------------------------------------------------------------------------
# Demo — mock data (no real astrophysical datasets required)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    rng = np.random.default_rng(42)
    output_dir = "astro_sonification"

    # 1. Galactic rotation
    r = np.linspace(1, 30, 60)  # kpc
    v_kep = 220.0 / np.sqrt(r / r[0])
    v_obs = np.where(r > 8, 220.0 + rng.normal(0, 5, len(r)), v_kep + rng.normal(0, 5, len(r)))
    ing_g = GalacticRotationIngestor(velocity_threshold=15.0)
    trits_g = ing_g.quantize(v_obs, v_kep)
    path = ing_g.render(trits_g, "galactic_rotation_cascade.wav", output_dir)
    print(f"[galactic]  trits={len(trits_g)}  +1={trits_g.count(1)}  0={trits_g.count(0)}  -1={trits_g.count(-1)}")
    print(f"            → {path}")

    # 2. Neutrino burst
    t_nu = np.linspace(0, 10, 200)  # seconds
    background = 10.0
    pmt = np.where((t_nu > 1) & (t_nu < 4), rng.poisson(80, 200).astype(float), rng.poisson(10, 200).astype(float))
    ing_n = JunoNeutrinoIngestor(spike_factor=3.0, veto_factor=0.5)
    trits_n = ing_n.quantize(pmt, background)
    path = ing_n.render(trits_n, "juno_neutrino_burst.wav", output_dir)
    print(f"[neutrino]  trits={len(trits_n)}  +1={trits_n.count(1)}  0={trits_n.count(0)}  -1={trits_n.count(-1)}")
    print(f"            → {path}")

    # 3. Pulsar
    phase = np.linspace(0, 4 * np.pi, 180)
    flux = 1.0 + 15.0 * np.exp(-((phase % (2 * np.pi) - np.pi / 2) ** 2) / 0.1) \
               + 5.0 * np.exp(-((phase % (2 * np.pi) - 3 * np.pi / 2) ** 2) / 0.2)
    ing_p = PulsarSignalIngestor(main_factor=5.0, inter_factor=2.0)
    trits_p = ing_p.quantize(flux, baseline_flux=1.0)
    path = ing_p.render(trits_p, "pulsar_signal_cascade.wav", output_dir)
    print(f"[pulsar]    trits={len(trits_p)}  +1={trits_p.count(1)}  0={trits_p.count(0)}  -1={trits_p.count(-1)}")
    print(f"            → {path}")

    print("\nTo validate conservation:")
    print("  from mcore_1.check_tree import check_tree")
    print("  weights = AstroSonifier.weights_for_check_tree(trits)")
    print("  results = check_tree(weights)")


__all__ = [
    "AstroSonifier",
    "GalacticRotationIngestor",
    "JunoNeutrinoIngestor",
    "PulsarSignalIngestor",
]
