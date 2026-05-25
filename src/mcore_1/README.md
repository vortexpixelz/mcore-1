# `mcore_1` — GJB2 / paper-oriented DNA carry + binary tree checker

This package is a **thin, explicit layer** for the GJB2 sonification paper and
`sibling` repo **gjb2-mcore-sonification**: DNA → trit encoding with T-bias, a
recursive **bisection** metrical tree, and post-order validation via the
existing **`mcore_py.checker.check_tree`**.

It does **not** replace `mcore_py` (prosodic model, overlays, MSS, etc.).

## Modules

| Module | Role |
|--------|------|
| `encoder.py` | `dna_to_trits`, per-step carry log; docstring states carry scan as **semigroup action** (not a monoid homomorphism from DNA concatenation). |
| `tree.py` | `build_binary_metrical_tree`, `build_post_deletion_frozen_tree`, `descendant_orig_indices`, `orig_span`. |
| `check_tree.py` | Delegates to `mcore_py.checker.check_tree`. |
| `errors.py` | Paper-facing `ErrorKind` names (CONSERVATION / OVERFLOW / EMPTY_CONSTITUENT). |

## Install

From the repo root (same `pyproject` as `mcore-py`):

```bash
python -m pip install -e ".[dev,analysis]"
```

Python **3.10+** is supported in line with the handoff; CI in this repo may use 3.11+.

## See also

- `HANDOFF_TO_GJB2.md` at repo root — commands and API for the other session.
- `tests/test_cascade.py`, `tests/test_associativity.py`.
