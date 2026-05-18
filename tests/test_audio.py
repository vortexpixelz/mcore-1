"""Tests for mcore_py.audio — Gaussian phonon synthesis and cochlear decoding."""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest

from mcore_py.audio import (
    ATOM_SAMPLES,
    SR,
    TRIT_FREQS,
    decode_atom_cochlear,
    decode_atom_fft,
    decode_wav,
    encode_wav,
    make_atom,
    read_wav,
    segment_atoms,
    synthesise,
    write_wav,
)


# ---------------------------------------------------------------------------
# Atom synthesis
# ---------------------------------------------------------------------------

def test_make_atom_shape():
    for trit in (0, 1, 2):
        atom = make_atom(trit)
        assert atom.shape == (ATOM_SAMPLES,), f"trit {trit}: expected 1920 samples"
        assert atom.dtype == np.float32


def test_make_atom_invalid():
    with pytest.raises(ValueError):
        make_atom(3)


def test_atom_peak_frequency():
    """Dominant FFT frequency must match the carrier."""
    for trit, expected_hz in TRIT_FREQS.items():
        atom = make_atom(trit)
        spec = np.abs(np.fft.rfft(atom, n=SR))
        freqs = np.fft.rfftfreq(SR, 1.0 / SR)
        peak_hz = freqs[np.argmax(spec)]
        assert abs(peak_hz - expected_hz) <= 2.0, (
            f"trit {trit}: peak at {peak_hz} Hz, expected {expected_hz} Hz")


def test_synthesise_length():
    trits = [0, 1, 2, 0, 2]
    audio = synthesise(trits)
    assert len(audio) == len(trits) * ATOM_SAMPLES


def test_synthesise_empty():
    assert len(synthesise([])) == 0


# ---------------------------------------------------------------------------
# WAV I/O
# ---------------------------------------------------------------------------

def test_wav_round_trip():
    trits = [0, 1, 2, 1, 0]
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = Path(f.name)
    write_wav(path, synthesise(trits))
    recovered, sr = read_wav(path)
    path.unlink()
    assert sr == SR
    assert len(recovered) == len(trits) * ATOM_SAMPLES


def test_segment_atoms():
    trits = [0, 1, 2]
    audio = synthesise(trits, normalise=False)
    atoms = segment_atoms(audio)
    assert len(atoms) == 3
    for a in atoms:
        assert len(a) == ATOM_SAMPLES


# ---------------------------------------------------------------------------
# Decoders — round-trip accuracy
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("trit", [0, 1, 2])
def test_fft_decoder_single_atom(trit):
    atom = make_atom(trit)
    assert decode_atom_fft(atom) == trit


@pytest.mark.parametrize("trit", [0, 1, 2])
def test_cochlear_decoder_single_atom(trit):
    atom = make_atom(trit)
    assert decode_atom_cochlear(atom) == trit


def test_decoders_agree_on_sequence():
    """FFT and cochlear decoders must agree on every atom of a random sequence."""
    rng = np.random.default_rng(42)
    trits = rng.integers(0, 3, size=20).tolist()
    audio = synthesise(trits, normalise=False)
    atoms = segment_atoms(audio)
    fft_out = [decode_atom_fft(a) for a in atoms]
    coch_out = [decode_atom_cochlear(a) for a in atoms]
    assert fft_out == coch_out, "FFT and cochlear decoders disagreed"
    assert fft_out == trits, "Decoder output did not match original trits"


# ---------------------------------------------------------------------------
# High-level encode_wav / decode_wav
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("method", ["fft", "cochlear"])
def test_encode_decode_wav_round_trip(method):
    trits = [0, 2, 1, 0, 1, 2]
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = Path(f.name)
    encode_wav(trits, path)
    recovered = decode_wav(path, method=method)
    path.unlink()
    assert recovered == trits, f"Round-trip failed with method={method}"
