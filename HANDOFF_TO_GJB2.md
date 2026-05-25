# Handoff: MCORE-1 tree checker (mcore-1 → gjb2-mcore-sonification)

This file is the **single handoff artifact** for integrating the new
**`mcore_1`** Python layer from **`vortexpixelz/mcore-1`** into the paper repo
**`vortexpixelz/gjb2-mcore-sonification`**.

Immutable read snapshot on **mcore-1**: tag **`mcore-1-v0.2-review-candidate`**
(merge of audit / Linear docs work).  Paper integration notes on your side:
`docs/MCORE1.md` on **`main`**.

---

## What was added (mcore-1)

Package path: **`src/mcore_1/`** (installed with the same editable install as
`mcore_py`).

| File | Purpose |
|------|---------|
| `encoder.py` | `dna_to_trits(dna) -> (trits, log)` — A=0, C=1, G=2, T=0, `ε_T=1` on T; `u=v+carry+ε_T`, `t=u%3`, `carry=u//3`. Docstring: **associative semigroup action** on carry state (not a monoid homomorphism from DNA to trit strings). |
| `tree.py` | `build_binary_metrical_tree`, `build_post_deletion_frozen_tree`, `build_frozen_after_deletion_trits`, `descendant_orig_indices`, `orig_span`, `frozen_weight_for_interval` (diagnostics). |
| `check_tree.py` | **Stable API:** `NodeResult`, `check_tree(weights, depth=...)`, `check_deletion(wt, mut, k)`; **`check_constituent(root)`** → `mcore_py.checker.CheckResult` for full `Constituent` trees. |
| `errors.py` | `ErrorKind` enum (CONSERVATION / OVERFLOW / EMPTY_CONSTITUENT) — mirrors checker categories for paper-facing prose. |
| `README.md` | Package-local overview. |

Tests:

- **`tests/test_cascade.py`** — carry cascade certificate (see caveats below).
- **`tests/test_node_api.py`** — stable `check_tree` / `check_deletion` / `NodeResult` API.

---

## Commands (mcore-1 repo)

```bash
cd /path/to/mcore-1
python -m pip install -e ".[dev,analysis]"
python -m pytest tests/test_cascade.py tests/test_associativity.py -q
```

Full suite:

```bash
python -m pytest -q
```

---

## API examples

### Encode DNA

```python
from mcore_1.encoder import dna_to_trits, iter_encode_steps

trits, log = dna_to_trits("ACGT")
assert len(trits) == len(log)
for step in iter_encode_steps("ACGT"):
    print(step.index, step.base, step.carry_in, step.trit, step.carry_out)
```

### Stable weight-stream API (preferred for gjb2 repo)

```python
from mcore_1.check_tree import NodeResult, check_tree, check_deletion

# Leaf trits only (0=S1, 1=S2, 2=S3); optional depth must equal ceil(log2(n))
rows: list[NodeResult] = check_tree([0, 1], depth=1)
for r in rows:
    print(r.node_id, r.leaf_lo, r.leaf_hi, r.valid, r.errors)  # errors ⊆ {"CONSERVATION","OVERFLOW"}

# WT vs mutant streams (same semantics as DNA helper, without re-encoding)
wt = [0, 1, 2, 0, 1, 2]       # length n
mut = [0, 1, 1, 2, 0]         # length n-1 after deletion at k
rows = check_deletion(wt, mut, deletion_pos_1=3)
```

### Build metrical tree + full ``mcore_py`` checker (``Constituent``)

```python
from mcore_1.tree import build_binary_metrical_tree
from mcore_1.check_tree import check_constituent
from mcore_1.encoder import dna_to_trits

trits, _ = dna_to_trits("ACGTACGT")
root = build_binary_metrical_tree(trits, list(range(1, len(trits) + 1)))
result = check_constituent(root)
assert result.valid
```

### Post-deletion “frozen certificate” tree (cascade lab)

```python
from mcore_1.tree import build_post_deletion_frozen_tree, descendant_orig_indices
from mcore_1.check_tree import check_constituent

dna = "ACGTACGTACGTACGTACGTACGTACGTAC"  # length 30 fixture used in tests
k = 12  # 1-based deletion site
root = build_post_deletion_frozen_tree(dna, k)
res = check_constituent(root)
assert not res.valid  # deliberate mismatch vs post-deletion re-encode

S = descendant_orig_indices(root)  # root's descendant original indices
print(S, len(res.errors))
```

Or equivalently without DNA objects:

```python
from mcore_1.encoder import dna_to_trits
from mcore_1.check_tree import check_deletion

dna = "ACGTACGTACGTACGTACGTACGTACGTAC"
k = 12
wt, _ = dna_to_trits(dna)
mut, _ = dna_to_trits(dna[: k - 1] + dna[k:])
rows = check_deletion(wt, mut, k)
```

**Semantics (frozen deletion check):** internal weights after deletion are set
by re-pooling **WT** trits at each surviving column using the **mutant**
bisection topology; leaves use **mutant** trits. Mismatches surface as
**CONSERVATION** / **OVERFLOW** on :class:`NodeResult` rows (other ``mcore_py``
error kinds still set ``valid=False`` but are omitted from the ``errors`` list).

This is **not** a second copy of `gjb2-mcore-sonification/code/checker.py`
(prefix associativity only); it is the **tree** checker wired to `mcore_py`.

---

## Theorem / test caveats (honest)

1. **Pooling ceiling:** under `(S1,S2,S3, +)` some subtrees hit **S3+S3 →
   OVERFLOW** even on prefixes where **carry did not change** individual leaf
   trits.  The certificate tests treat “no drift **left** of *k*” as **no
   CONSERVATION** errors on that prefix; **OVERFLOW** may still appear (partial
   semigroup artefact).

2. **Hull predicate for “contains deletion site”:** tests use
   `min(descendants) <= k <= max(descendants)` on **original** 1-based indices.
   Endpoints **`k in {1, n}`** are covered by a separate smoke test because
   the bisection hull of survivors may not bracket the deleted column the same
   way as interior cuts.

3. **Theorem (iii)** in `test_theorem_3_shallowest_failure_near_leaf` is checked
   for **`k` in `2..n-1`** only (same hull reason).

---

## Suggested integration steps (gjb2 repo)

1. Depend on **mcore-1** as a git submodule, editable install, or copied
   subtree—**do not** fork `dna_to_trits` with different carry rules.
2. Keep **`code/checker.py`** as the **linear** prefix associativity checker.
3. Call **`mcore_1.check_tree.check_tree(weights)`** / **`check_deletion`** from the paper code, or **`check_constituent`** when you already hold a ``Constituent`` tree.
   where the paper needs the **binary metrical tree** certificate.
4. Cite **mcore-1** tag **`mcore-1-v0.2-review-candidate`** for reproducibility.

---

## Links

- **Upstream repo:** https://github.com/vortexpixelz/mcore-1  
- **Paper repo:** https://github.com/vortexpixelz/gjb2-mcore-sonification  
- **This handoff file (mcore-1):** `HANDOFF_TO_GJB2.md` (repo root)
