# mcore-py

**MCORE-1: Metrical Core Representation** — a language-agnostic data model for prosodic structure with ternary weight algebra, compact binary encoding, and tradition-specific overlays.

Reference implementation of the [MCORE-1 Specification v0.1](docs/MCORE-1-v0.1-spec.pdf) (March 2026).

## What is this?

Existing metrical annotation systems (TEI, ToBI) share three limitations: they assume binary syllable weight, they can't express or verify the constraints that generate patterns, and they have no machine-readable in-band encoding. MCORE-1 addresses all three.

The core idea: **ternary weight** (light / heavy / superheavy) as a primitive, with a formal **trit algebra** that supports both analysis ("is this line well-formed?") and generation ("what are all valid lines for this meter?"). The system is extensible via **tradition-specific overlays** — Sanskrit, Greek, Arabic, Chinese, and Japanese prosody all map onto the same algebra.

## Quick start

```bash
pip install -e ".[dev]"

# Validate a metrical pattern (digit notation: 0=light, 1=heavy, 2=superheavy)
python -m mcore_py.cli validate "01"
# VALID: u –  (total weight: S3)

# Generate all 3-position patterns with total weight S3
python -m mcore_py.cli complete 3 2
# Found: 6
#   u u ≡
#   u – –
#   u ≡ u
#   – u –
#   – – u
#   ≡ u u

# Encode as Base64-TME
python -m mcore_py.cli encode "01" -a
#   F  (15)  TP_S1_N
#   I  (18)  TP_S2_N

# Decode the spec example
python -m mcore_py.cli decode "B810C" -a
#   B  (11)  PUSH_FRAME
#   8  ( 8)  SET_LEVEL_2
#   1  ( 1)  SET_WEIGHT_S2
#   0  ( 0)  SET_WEIGHT_S1
#   C  (12)  POP_FRAME
```

## Architecture

```
MCORE-1                  Language-agnostic data model
  ├── Trit Algebra       T = {0,1,2}, +, ×, π_L, *
  ├── Overlays           QuantitativeMetrics (IE) | Arabic | Chinese | Japanese
  ├── TME-6              6-bit packed binary (64 opcodes)
  ├── Base64-TME         Text-safe serialization
  ├── MSS                Human-readable surface syntax: \TME[1:W:2]
  └── MRP Renderers      Terminal | Audio | TokenStream
```

## Python API

```python
from mcore_py import (
    Trit, Tension, Level, ProsodicUnit, Constituent, Budget,
    trit_add, complete, check_tree,
    to_base64tme, from_base64tme,
    parse_mss, emit_mss,
)
from mcore_py.overlays import QuantitativeMetrics

# Build a foot: heavy + light = S3
foot = Constituent(
    parent=ProsodicUnit(weight=Trit.S3, level=Level.L2_GANA),
    children=[
        ProsodicUnit(weight=Trit.S2, level=Level.L1_AKSARA),
        ProsodicUnit(weight=Trit.S1, level=Level.L1_AKSARA),
    ],
)

# Validate mora conservation
result = check_tree(foot)
assert result.valid  # ✓ S2 + S1 = S3

# Generate all valid 4-position iambic patterns
from mcore_py.algebra import enumerate_patterns
budget = Budget(min_weight=Trit.S2, max_weight=Trit.S2, exact=True)
patterns = enumerate_patterns(4, budget)
```

## Conformance levels

| Level | Name       | Status | Contents |
|-------|------------|--------|----------|
| 1     | Core       | ✓      | Data model, trit algebra (+, ×, π_L), checker |
| 2     | Encoding   | ✓      | TME-6, Base64-TME, MSS parsing |
| 3     | Generation | ✓      | Completion operator + QuantitativeMetrics overlay |
| 4     | Full       | ◐      | Terminal + TokenStream renderers (audio TBD) |

## Key references

- Faust & Ulfsbjorninn (2025). "The three degrees of metrical strength." *J. Linguistics* 61(4).
- Kiparsky (2018). "Indo-European Origins of the Greek Hexameter." In *Sprache und Metrik*. Brill.
- Pingala. *Chandahsastra* (c. 2nd century BCE). Foundational text on Sanskrit prosody.
- Kager (1989). *A Metrical Theory of Stress and Destressing*. Foris.

## License

MIT

## Author

Jacob Walker · [Symonic LLC](https://github.com/vortexpixelz) · [@WalkerJaco38855](https://x.com/WalkerJaco38855)
