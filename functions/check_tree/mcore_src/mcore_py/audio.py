"""
mcore_py.audio
==============

Gaussian phonon wavepacket synthesis and cochlear tonotopic decoding for
MCORE-1 trit sequences.

The three trit carriers (S1=800 Hz, S2=1600 Hz, S3=3200 Hz) are octave-spaced,
so each sits at a distinct cochlear "place."  The biological decoder below
mirrors what the basilar membrane + inner hair cells do in vivo: three parallel
bandpass channels whose energy readout determines which place is activated.

References
----------
- Gabor, D. (1946). Theory of communication. JIEE 93(26):429-457.
- Slaney, M. (1993). Apple Tech Report 35: Auditory Toolbox.
- gjb2-mcore-sonification: synthesis reference implementation.
"""

from __future__ import annotations

import struct
import wave
from pathlib import Path
from typing import Literal

import numpy as np

try:
    from scipy import signal as sp_signal
    _SCIPY = True
except ImportError:
    _SCIPY = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SR: int = 48_000
ATOM_SAMPLES: int = 1_920       # 40 ms at 48 kHz
ATOM_DUR: float = 0.040         # seconds
SIGMA_GAUSS: float = 0.008      # Gaussian sigma (s)
MU_GAUSS: float = 0.020         # Gaussian centre (s)
AMPLITUDE: float = 0.8          # peak amplitude

TRIT_FREQS: dict[int, float] = {0: 800.0, 1: 1600.0, 2: 3200.0}

# Cochlear filterbank parameters
COCHLEAR_BW: float = 80.0       # per-channel bandwidth (Hz)
COCHLEAR_ORDER: int = 6         # Butterworth filter order

# Pre-computed Gabor time axis (module-level, shared across all atoms)
_T = np.linspace(0.0, ATOM_DUR, ATOM_SAMPLES, endpoint=False)
_GAUSS_ENVELOPE = AMPLITUDE * np.exp(-0.5 * ((_T - MU_GAUSS) / SIGMA_GAUSS) ** 2)


# ---------------------------------------------------------------------------
# Atom synthesis
# ---------------------------------------------------------------------------

def make_atom(trit: int) -> np.ndarray:
    """Return a 1920-sample float32 Gabor atom for the given trit (0, 1, or 2)."""
    if trit not in TRIT_FREQS:
        raise ValueError(f"trit must be 0, 1, or 2; got {trit!r}")
    f0 = TRIT_FREQS[trit]
    return (_GAUSS_ENVELOPE * np.sin(2.0 * np.pi * f0 * _T)).astype(np.float32)


def synthesise(trits: list[int], normalise: bool = True) -> np.ndarray:
    """Concatenate trit atoms into a float32 audio signal."""
    if not trits:
        return np.zeros(0, dtype=np.float32)
    audio = np.concatenate([make_atom(t) for t in trits]).astype(np.float32)
    if normalise:
        peak = np.max(np.abs(audio))
        if peak > 0:
            audio /= peak
    return audio


# ---------------------------------------------------------------------------
# WAV I/O
# ---------------------------------------------------------------------------

def write_wav(path: str | Path, audio: np.ndarray, sr: int = SR) -> None:
    """Write float32 or int16 audio to a 16-bit PCM WAV file."""
    path = Path(path)
    if audio.dtype != np.int16:
        pcm = (audio * 32767).clip(-32768, 32767).astype(np.int16)
    else:
        pcm = audio
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def read_wav(path: str | Path) -> tuple[np.ndarray, int]:
    """Return (float32 samples, sample_rate) from a WAV file."""
    with wave.open(str(path), "r") as wf:
        sr = wf.getframerate()
        n_frames = wf.getnframes()
        n_channels = wf.getnchannels()
        raw = wf.readframes(n_frames)
    dtype = np.int16 if wf.getsampwidth() == 2 else np.int8
    samples = np.frombuffer(raw, dtype=dtype)
    if n_channels > 1:
        samples = samples[::n_channels]
    return samples.astype(np.float32) / 32768.0, sr


def segment_atoms(audio: np.ndarray, atom_samples: int = ATOM_SAMPLES) -> list[np.ndarray]:
    """Slice a contiguous audio signal into a list of fixed-length atoms."""
    n = len(audio) // atom_samples
    return [audio[i * atom_samples:(i + 1) * atom_samples] for i in range(n)]


# ---------------------------------------------------------------------------
# Decoders
# ---------------------------------------------------------------------------

# -- FFT decoder (classical) ------------------------------------------------

_N_PAD: int = SR  # zero-pad to 1 s -> 1 Hz resolution

def decode_atom_fft(atom: np.ndarray) -> int:
    """Classify a trit atom via zero-padded FFT bin lookup.

    3-step process:
    1. Zero-pad to N_PAD samples for sub-Hz resolution.
    2. Look up FFT magnitude at the three carrier bins.
    3. Return argmax (0=S1, 1=S2, 2=S3).
    """
    padded = np.zeros(_N_PAD, dtype=np.float64)
    padded[:len(atom)] = atom
    spec = np.abs(np.fft.rfft(padded))
    powers = []
    for f0 in (800.0, 1600.0, 3200.0):
        idx = int(round(f0 * _N_PAD / SR))
        powers.append(spec[max(0, idx - 2):idx + 3].max())
    return int(np.argmax(powers))


# -- Cochlear decoder (tonotopic filterbank) --------------------------------

def _build_cochlear_filters() -> list:
    """Pre-compute SOS Butterworth BPF coefficients for all three trit channels."""
    if not _SCIPY:
        raise ImportError("scipy is required for cochlear decoding: pip install scipy")
    filters = []
    for f0 in (800.0, 1600.0, 3200.0):
        low = f0 - COCHLEAR_BW / 2.0
        high = f0 + COCHLEAR_BW / 2.0
        sos = sp_signal.butter(COCHLEAR_ORDER, [low, high],
                               btype="bandpass", fs=SR, output="sos")
        filters.append(sos)
    return filters


_COCHLEAR_FILTERS: list | None = None


def _get_cochlear_filters() -> list:
    global _COCHLEAR_FILTERS
    if _COCHLEAR_FILTERS is None:
        _COCHLEAR_FILTERS = _build_cochlear_filters()
    return _COCHLEAR_FILTERS


def decode_atom_cochlear(atom: np.ndarray) -> int:
    """Classify a trit atom via cochlear tonotopic filterbank.

    Biologically faithful model of basilar-membrane place coding:
    - Three parallel Butterworth BPF channels at trit carrier frequencies.
    - Hilbert-envelope RMS² energy per channel mimics inner hair-cell output.
    - Argmax of channel energies = decoded trit (0=S1, 1=S2, 2=S3).

    Advantages over FFT decoder:
    - No zero-padding required.
    - Streaming / real-time compatible.
    - Directly maps to SpiralE-style in-ear BCI electrode placement.
    """
    filters = _get_cochlear_filters()
    energies = []
    for sos in filters:
        filtered = sp_signal.sosfilt(sos, atom.astype(np.float64))
        envelope = np.abs(sp_signal.hilbert(filtered))
        energies.append(float(np.mean(envelope ** 2)))
    return int(np.argmax(energies))


# ---------------------------------------------------------------------------
# High-level encode / decode API
# ---------------------------------------------------------------------------

Method = Literal["fft", "cochlear"]


def encode_wav(trits: list[int], output: str | Path, normalise: bool = True) -> Path:
    """Synthesise trit sequence → WAV file.  Returns the output path."""
    output = Path(output)
    audio = synthesise(trits, normalise=normalise)
    write_wav(output, audio)
    return output


def decode_wav(path: str | Path, method: Method = "cochlear") -> list[int]:
    """Decode a WAV file to a trit list using the chosen method.

    Parameters
    ----------
    path : str or Path
        Path to a WAV file produced by encode_wav (or gjb2_sonification.py).
    method : "fft" | "cochlear"
        "fft"      — zero-padded FFT bin lookup (classical)
        "cochlear" — Butterworth BPF + Hilbert energy (tonotopic / biological)
    """
    audio, sr = read_wav(path)
    if sr != SR:
        raise ValueError(f"Expected {SR} Hz; got {sr} Hz. Resample first.")
    atoms = segment_atoms(audio)
    decoder = decode_atom_cochlear if method == "cochlear" else decode_atom_fft
    return [decoder(a) for a in atoms]
