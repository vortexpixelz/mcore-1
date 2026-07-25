# MCORE-1 Acoustic Quantum / Genomic Sonification Extension
## Specification v0.2 — Acoustic Quantum Gateway Layer

**Repository:** https://github.com/vortexpixelz/mcore-1
**Author:** Jacob Walker / Symonic LLC
**Date:** 2026-05-18
**Status:** Research prototype

---

## 0. Reality Anchor

This specification describes an engineering roadmap, not a finished system.
The encoding/decoding layer (DNA → WAV → cochlear filterbank) is **implemented and empirically verified** in this repository.
The effector layer (phonons → DNA/RNA alteration) is the research frontier —
it maps onto active sonogenetics and focused-ultrasound literature and is explicitly marked as such.

No claim is made that audio playback alters DNA in unengineered tissue.

---

## 1. Pipeline Overview

```
DNA/RNA sequence (e.g. GJB2 wildtype / c.35delG frameshift)
    │
    ▼  MCORE-1 trit algebra (dna_to_mcore_trits)
Trit sequence [0, 1, 2, ...]
    │
    ▼  Gaussian phonon wavepacket synthesis (mcore_py.audio.encode_wav)
WAV file  ─  concatenated 40 ms Gabor atoms at 800 / 1600 / 3200 Hz
    │
    ▼  AirPods Pro (H2 chip) — 48 kHz lossless, spatial audio, head-tracked
Ear canal
    │
    ▼  SpiralE in-ear BCI electrode array  OR  cochlear tonotopic filterbank
       (mcore_py.audio.decode_wav  method="cochlear")
Decoded trit sequence — step-function mismatch at mutation site
    │
    ▼  [RESEARCH FRONTIER — not yet implemented in this repo]
Microtubule / ordered-water phonon substrate
Cold-plasma / sonofusion micro-events (Purdue EPPL lineage)
AlphaFold 3 sonosensitive protein–DNA interface design
    │
    ▼
Targeted epigenetic shift or gene-expression change
    ↔  Closed-loop readout via SpiralE
```

---

## 2. Implemented Layer (v0.2.0)

### 2.1 Phonon Wavepacket — `mcore_py.audio`

| Parameter | Value |
|-----------|-------|
| Sample rate | 48 000 Hz |
| Atom duration | 40 ms (1 920 samples) |
| Gaussian σ | 0.008 s |
| Gaussian μ | 0.020 s |
| Amplitude | 0.8 |
| S1 carrier | 800 Hz |
| S2 carrier | 1 600 Hz |
| S3 carrier | 3 200 Hz |
| Gabor uncertainty product | σ_t × σ_f = 0.0895 (1/(4π) ≈ 0.0796, ×1.12) |

**Empirical result (gabor_analysis.ipynb §2):** atoms sit within 12% of the Heisenberg–Gabor uncertainty bound. An independent estimator in `gjb2-mcore-sonification` (`code/analysis.py::_time_freq_sigmas`, 2 s zero-pad rather than 1 s) gives 0.0896 (×1.13), agreeing to four decimal places per trit.

### 2.2 FFT Decoder

- Zero-pad each 1,920-sample atom to 48,000 samples (`_N_PAD = SR`), giving 1 Hz FFT bin resolution
- Read magnitude at bins {800, 1,600, 3,200} Hz using a ±2-bin / ±2 Hz local window
- Argmax over carrier magnitudes → decoded trit
- 100% round-trip accuracy on clean WAVs in current tests

### 2.3 Cochlear Tonotopic Filterbank Decoder

Biological reference model of basilar-membrane place coding:

```python
from mcore_py.audio import decode_atom_cochlear

trit = decode_atom_cochlear(atom_1920_samples)  # 0, 1, or 2
```

| Stage | Cochlea | Software |
|-------|---------|----------|
| Spectral split | Basilar membrane resonance | Butterworth BPF (6-pole, BW=80 Hz) |
| Energy readout | Inner hair-cell receptor potential | Hilbert envelope → RMS² |
| Classification | Auditory-nerve place code | argmax(energies) |

**Empirical result (gabor_analysis.ipynb §7):** 100% agreement with FFT decoder across all 2 041 atoms in three WAVs.

No zero-padding required. Streaming/real-time compatible. Direct mapping to SpiralE electrode placement.

### 2.4 CLI

```bash
# Synthesise trit sequence → WAV
mcore audio encode 012102012 --output mutation.wav

# Decode WAV → trits (cochlear method, default)
mcore audio decode gjb2_wildtype.wav --method cochlear

# Decode with FFT method, save JSON
mcore audio decode delta_c35delG.wav --method fft --output trits.json
```

---

## 3. Theoretical Foundations

### 3.1 Gabor–Heisenberg Uncertainty

Each trit atom is a Gabor elementary function: a Gaussian-windowed sinusoid
that achieves (or approaches) the minimum time-frequency uncertainty tile.

$$\sigma_t \cdot \sigma_f \geq \frac{1}{4\pi} \approx 0.0796$$

The octave-spaced carriers (800 → 1 600 → 3 200 Hz) place each atom at a
distinct, non-overlapping tile in the time-frequency plane — exactly what
the basilar membrane achieves via tonotopy.

### 3.2 Cochlear Place Coding

The basilar membrane is a biological Gabor spectrometer:
- High frequencies respond near the base; low frequencies near the apex.
- Outer hair cells (prestin motor protein) provide active amplification
  and sharp tuning (~1 ERB bandwidth per place).
- Inner hair cells convert basilar-membrane velocity → auditory-nerve firing rate.

The three trit carriers fall at well-separated cochlear places (octave spacing
exceeds any realistic ERB bandwidth at 800–3 200 Hz), so cross-channel interference
is negligible under any physiologically plausible condition.

### 3.3 Genomic Sonification

Trit encoding of DNA sequences:

| Nucleotide pair | Trit | Carrier |
|----------------|------|---------|
| Low-complexity / synonymous | 0 (S1) | 800 Hz |
| Moderate divergence | 1 (S2) | 1 600 Hz |
| High divergence / frameshift | 2 (S3) | 3 200 Hz |

Delta WAVs encode `(mutation_trit − wildtype_trit) % 3` per position.
Trit 0 = no change; trit 1 or 2 = mismatch.
The GJB2 c.35delG frameshift produces a step function: trit=0 upstream of
position 35, then roughly 60% trit≠0 downstream (measured 0.598 for c.35delG
and 0.602 for c.235delC in `gabor_analysis.ipynb` §4; the exact prefix-aligned
comparison in `gjb2-mcore-sonification` gives 0.605 and 0.613).

---

## 4. Research Frontier (Not Yet Implemented)

The following gaps must be closed to extend the pipeline beyond decoding:

### Gap 1 — Frequency / Energy Scale

Audible-phonon carriers (kHz) are 6–9 orders of magnitude below the GHz–THz
collective modes of DNA/protein. No established nonlinear up-conversion
mechanism bridges this range in unengineered biological tissue.

**Research path:** Sonogenetics (Salk Institute / 2023–2025) uses ultrasound-activated
mechanosensitive channels (TRPV4, TRP-4) or heat-shock promoters for gene activation.
Requires prior genetic insertion of sonosensors. Would allow MCORE trit sequences
to control gene expression if sonosensitive cells are pre-engineered.

### Gap 2 — Intensity

AirPods Pro output: ~microwatts at the eardrum.
Therapeutic focused ultrasound for BBB opening: W/cm² with microbubbles.
A biological amplifier chain (prestin → microtubule phonon super-radiance) is
hypothesised but not experimentally demonstrated for audible-frequency input.

### Gap 3 — Coherence

Orch-OR / QBD frameworks predict microtubule phonon coherence, but estimated
decoherence times in warm/wet conditions are femtoseconds (Tegmark 2000).
Classical activity-dependent gene expression (neural firing → immediate-early genes)
is well established but does not require quantum coherence.

### Gap 4 — Targeting

AirPods + spatial audio: excellent perceptual targeting, not cellular specificity.
SpiralE: entry-point readout at the cochlea, not genomic delivery.

**AlphaFold 3 bridge:** AF3 predicts protein–DNA/RNA/ligand complexes with
near-experimental accuracy. Seeding MD/vibronic simulations from AF3 structures
could identify sonosensitive interfaces tunable to specific trit frequencies.

---

## 5. Module Roadmap

| Version | Deliverable |
|---------|-------------|
| **v0.2.0** (current) | `mcore_py.audio` — Gaussian atom synthesis, cochlear filterbank, WAV I/O, `mcore audio` CLI |
| v0.3.0 | Binaural rendering stub + spatial-audio metadata export (SOFA / HRTFs) |
| v0.4.0 | Sonogenetics parameter-sweep notebook (sonosensor resonance vs trit carriers) |
| v0.5.0 | AlphaFold 3 interface design notebook (vibronic mode extraction from AF3 predictions) |
| v1.0 | Full wet-lab sonogenetics protocol spec (pre-engineered sonosensitive cell line) |

---

## 6. Safety / Integrity Statement

This specification is for defensive academic research only.

It does not provide:
- practical SHA-256 preimage attacks
- genome modification tooling for use in unengineered organisms
- clinical or therapeutic advice
- claims that audio playback alters DNA in standard biological tissue

All effector-layer statements are clearly labelled as research frontiers.
The encoding/decoding layer is the only implemented and empirically validated component.

---

*MCORE-1 / Symonic LLC — Acoustic Quantum Gateway Specification*
