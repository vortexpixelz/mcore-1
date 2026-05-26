# astro-mcore-ingestor

**Reusable MCORE-1 skill — astrophysical time-series → trit algebra + fractal cascade**

> ⚠️ **EXPERIMENTAL** — This is a research-program extension layer.
> The genomic (GJB2) core is validated. Astrophysical domains are unvalidated against
> external MHD/PIC benchmarks. See Claim Status table before citing.

---

## Claim Status

| Claim | Status |
|---|---|
| Deterministic trit quantization (pure rule-based functions, no hidden state) | **[ESTABLISHED]** |
| Gabor render mirrors `gjb2_sonification.py` production pattern (integer indexing, np.concatenate, -0.5 dBFS) | **[ESTABLISHED]** |
| `weights_for_check_tree` shift preserves MCORE-1 mora-pooling invariant | **[ESTABLISHED]** |
| Trit sequences from these ingestors will surface CONSERVATION/OVERFLOW errors in `check_tree` | **[PLAUSIBLE]** — not yet verified cross-domain |
| Acoustic output meaningfully represents physical dark matter / neutrino / pulsar dynamics | **[CONJECTURAL]** — future validation work required |

---

## Overview

Three deterministic ingestor classes that map real astrophysical observations into
the canonical MCORE-1 `{-1, 0, +1}` topology and render via depth-aware Gabor sonification.

| Class | Domain | `+1` | `0` | `-1` |
|---|---|---|---|---|
| `GalacticRotationIngestor` | Dark matter halo | Excess velocity | Baryonic-consistent | Anomalous drag |
| `JunoNeutrinoIngestor` | Supernova neutrino burst | 3σ PMT spike | Baseline background | Dead-time veto |
| `PulsarSignalIngestor` | Neutron star radio beam | Main pulse | Off-pulse (current sheet) | Interpulse |

All three inherit from `AstroSonifier` which provides:
- `render(signed_trits, filename)` — production Gabor renderer
- `weights_for_check_tree(signed_trits)` — shift to unsigned `{0,1,2}` for `check_tree`

---

## Conservation Bridge

The MCORE-1 algebra operates on `T = {S1, S2, S3} ≡ {0, 1, 2}` (unsigned).
These ingestors output signed `{-1, 0, +1}`. Before calling `check_tree`:

```python
from mcore_1.check_tree import check_tree
weights = AstroSonifier.weights_for_check_tree(signed_trits)  # shift +1
results = check_tree(weights)
```

The mora-pooling invariant: `w(parent) = trit_add_seq([w(c1), w(c2), ...])` under
the partial commutative semigroup `(T, +)`. CONSERVATION and OVERFLOW errors
indicate topology violations in the discrete cascade.

---

## Sonification Parameters

Matches `gjb2_sonification.py` production discipline:

| Depth | Event | Freq (Hz) | σ (s) | Amplitude |
|---|---|---|---|---|
| 0 | Primary tearing | 880 | 0.002 | 0.40 |
| 1 | Secondary crackle | 1320 | 0.0015 | 0.25 |
| 2 | Tertiary micro-pop | 1980 | 0.001 | 0.10 |
| neutral | Tension hum | 60 | 1.0 | 0.05 |

---

## Quick Start

```python
from experimental.astro_ingestor.astro_mcore_ingestor import (
    GalacticRotationIngestor,
    JunoNeutrinoIngestor,
    PulsarSignalIngestor,
    AstroSonifier,
)
import numpy as np

# Galactic rotation
ing = GalacticRotationIngestor(velocity_threshold=15.0)
trits = ing.quantize(observed_velocity_array, keplerian_velocity_array)
path = ing.render(trits, "my_galaxy.wav")

# Validate conservation
from mcore_1.check_tree import check_tree
weights = AstroSonifier.weights_for_check_tree(trits)
results = check_tree(weights)
```

---

## Integration

- **mcore-appwrite**: pipe `weights_for_check_tree(trits)` to the deployed `check_tree` Appwrite function
- **deterministic-systems**: quantizers are pure functions — suitable for formal verification
- **gjb2-mcore-sonification**: output WAV format identical, suitable for same analysis pipeline

---

## Future Validation Work

- Ingest real SPARC/THINGS galactic rotation curves; compare trit lesion maps with NFW/Burkert halo fits
- Process JUNO/Super-K supernova simulation datasets; validate 3σ detection reproduces known light-curve features
- Feed generated trit sequences into deployed `mcore_check_tree` Appwrite function for cross-domain conservation verification
- Benchmark against MHD/PIC simulation outputs before any physical fidelity claims enter the whitepaper

---

## Files

- `astro_mcore_ingestor.py` — Main implementation
- `SKILL.md` — This file

---

## Author

Jacob Walker — MCORE-1 / Origami Axioms research program (Symonic / ArchēLab), May 2026  
Pop-frame audit: Perplexity Arche Translator, Turn 3
